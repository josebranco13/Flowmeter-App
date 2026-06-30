from __future__ import annotations

import json
import os
import socket
from dataclasses import dataclass
from datetime import datetime, timezone
from threading import Event
from typing import Any, Mapping
from uuid import NAMESPACE_URL, uuid4, uuid5
from pathlib import Path


DEFAULT_TOPIC = "flowmeter/measurements"

BASE_DIR = Path(__file__).resolve().parent.parent
MQTT_CONFIG_PATH = BASE_DIR / "data" / "mqtt_config.json"


class MqttError(RuntimeError):
    """Erro controlado relacionado com a configuração ou o envio MQTT."""


class MqttConfigurationError(MqttError):
    """Configuração MQTT inválida ou incompleta."""


class MqttPublishError(MqttError):
    """Não foi possível confirmar o envio da mensagem ao broker MQTT."""


@dataclass(frozen=True, slots=True)
class MqttSettings:
    """
    Configuração obtida através de variáveis de ambiente.

    Variáveis suportadas:
      FLOWMETER_MQTT_BROKER       Obrigatória. IP ou hostname do broker.
      FLOWMETER_MQTT_PORT         Opcional. Por omissão: 1883.
      FLOWMETER_MQTT_TOPIC        Opcional. Por omissão: flowmeter/measurements.
      FLOWMETER_MQTT_USERNAME     Opcional.
      FLOWMETER_MQTT_PASSWORD     Opcional.
      FLOWMETER_MQTT_USE_TLS      Opcional: true/false. Por omissão: false.
      FLOWMETER_MQTT_CA_CERT      Opcional. Caminho para o certificado CA.
      FLOWMETER_SENSOR_ID         Opcional. Por omissão: YF-S201-01.
      FLOWMETER_MACHINE_ID        Opcional. Por omissão: MACHINE-01.
    """

    broker_host: str
    broker_port: int = 1883
    topic: str = DEFAULT_TOPIC
    username: str | None = None
    password: str | None = None
    use_tls: bool = False
    ca_cert: str | None = None
    sensor_id: str = "YF-S201-01"
    machine_id: str = "MACHINE-01"
    keepalive_seconds: int = 60
    connect_timeout_seconds: float = 8.0
    publish_timeout_seconds: float = 8.0

    @classmethod
    def from_file(cls) -> "MqttSettings":
        if not MQTT_CONFIG_PATH.exists():
            raise MqttConfigurationError(
                f"O ficheiro de configuração MQTT não existe: "
                f"{MQTT_CONFIG_PATH}"
            )

        try:
            with MQTT_CONFIG_PATH.open("r", encoding="utf-8") as file:
                data = json.load(file)
        except (OSError, json.JSONDecodeError) as error:
            raise MqttConfigurationError(
                "Não foi possível ler o ficheiro de configuração MQTT."
            ) from error

        broker_host = str(data.get("broker_host", "")).strip()

        if not broker_host:
            raise MqttConfigurationError(
                "O endereço do broker MQTT não está configurado."
            )

        try:
            broker_port = int(data.get("broker_port", 1883))
        except (TypeError, ValueError) as error:
            raise MqttConfigurationError(
                "A porta MQTT tem de ser um número inteiro."
            ) from error

        topic = str(
            data.get("topic", "flowmeter/measurements")
        ).strip()

        if not topic:
            raise MqttConfigurationError(
                "O tópico MQTT não pode estar vazio."
            )

        return cls(
            broker_host=broker_host,
            broker_port=broker_port,
            topic=topic,
            username=data.get("username") or None,
            password=data.get("password") or None,
            use_tls=bool(data.get("use_tls", False)),
            ca_cert=data.get("ca_cert") or None,
            sensor_id=str(
                data.get("sensor_id", "YF-S201-01")
            ).strip(),
            machine_id=str(
                data.get("machine_id", "MACHINE-01")
            ).strip(),
        )


def _environment_boolean(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default

    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "sim", "on"}:
        return True
    if normalized in {"0", "false", "no", "nao", "não", "off"}:
        return False

    raise MqttConfigurationError(
        f"{name} deve ter um valor booleano, por exemplo true ou false."
    )


def build_measurement_payload(
    session: Mapping[str, Any],
    measurement: Mapping[str, Any],
    settings: MqttSettings,
) -> dict[str, Any]:
    """
    Constrói uma mensagem JSON para uma única medição/circuito.

    O message_id é determinístico. Se a mesma medição for reenviada,
    o Node-RED pode usar este campo para detetar e ignorar duplicados.
    """

    session_id = str(
        measurement.get("session_id")
        or session.get("session_id")
        or ""
    )
    operator = str(
        measurement.get("operador")
        or session.get("operador")
        or ""
    )
    mold = str(
        measurement.get("molde")
        or session.get("molde")
        or ""
    )
    mold_side = str(
        measurement.get("lado")
        or session.get("lado_molde")
        or ""
    )
    diameter = (
        measurement.get("diametro_mm")
        if measurement.get("diametro_mm") is not None
        else session.get("diametro_mm")
    )
    inlet_pressure = (
        measurement.get("pressao_entrada_bar")
        if measurement.get("pressao_entrada_bar") is not None
        else session.get("pressao_entrada_bar")
    )
    circuit = measurement.get("circuito")
    measured_at = str(
        measurement.get("medido_em")
        or session.get("atualizado_em")
        or session.get("criado_em")
        or ""
    )

    identity = "|".join(
        (
            session_id,
            mold_side,
            str(circuit or ""),
            measured_at,
        )
    )
    message_id = uuid5(NAMESPACE_URL, identity).hex

    return {
        "schema_version": 1,
        "message_type": "flow_measurement",
        "message_id": message_id,
        "sensor_id": settings.sensor_id,
        "machine_id": settings.machine_id,
        "session_id": session_id,
        "operator": operator,
        "mold": mold,
        "mold_side": mold_side,
        "circuit_diameter": diameter,
        "inlet_pressure_bar": inlet_pressure,
        "circuit": circuit,
        "readings": {
            "flow_min_l_min": measurement.get("caudal_min_l_min"),
            "flow_average_l_min": measurement.get("caudal_medio_l_min"),
            "flow_max_l_min": measurement.get("caudal_max_l_min"),
            "sample_count": measurement.get("amostras"),
        },
        "measured_at": measured_at,
        "sent_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }


def publish_json(
    payload: Mapping[str, Any],
    settings: MqttSettings | None = None,
) -> str:
    """
    Publica um dicionário como JSON com QoS 1 e aguarda a confirmação
    do broker antes de devolver o controlo à aplicação.

    Devolve o message_id. Em caso de falha, lança MqttError.
    """

    settings = settings or MqttSettings.from_file()

    try:
        from paho.mqtt import client as mqtt
    except ImportError as error:
        raise MqttConfigurationError(
            "A biblioteca paho-mqtt não está instalada. "
            "Execute: python -m pip install paho-mqtt"
        ) from error

    try:
        encoded_payload = json.dumps(
            dict(payload),
            ensure_ascii=False,
            separators=(",", ":"),
            allow_nan=False,
        )
    except (TypeError, ValueError) as error:
        raise MqttPublishError(
            "A medição contém dados que não podem ser convertidos para JSON."
        ) from error

    connected = Event()
    connection_error: list[str] = []

    def on_connect(
        client: Any,
        userdata: Any,
        flags: Any,
        reason_code: Any,
        properties: Any,
    ) -> None:
        if getattr(reason_code, "is_failure", False):
            connection_error.append(str(reason_code))
        connected.set()

    client_id = (
        f"flowmeter-{socket.gethostname()}-{uuid4().hex[:8]}"
    )
    client = mqtt.Client(
        callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
        client_id=client_id,
        protocol=mqtt.MQTTv311,
    )
    client.on_connect = on_connect

    if settings.username:
        client.username_pw_set(
            settings.username,
            settings.password or "",
        )

    if settings.use_tls:
        client.tls_set(ca_certs=settings.ca_cert)
        client.tls_insecure_set(False)

    loop_started = False

    try:
        client.connect(
            settings.broker_host,
            settings.broker_port,
            settings.keepalive_seconds,
        )
        client.loop_start()
        loop_started = True

        if not connected.wait(settings.connect_timeout_seconds):
            raise MqttPublishError(
                "O broker MQTT não respondeu dentro do tempo limite."
            )

        if connection_error:
            raise MqttPublishError(
                "O broker MQTT recusou a ligação: "
                + connection_error[0]
            )

        publication = client.publish(
            settings.topic,
            payload=encoded_payload,
            qos=1,
            retain=False,
        )

        if publication.rc != mqtt.MQTT_ERR_SUCCESS:
            raise MqttPublishError(
                f"O pedido de publicação falhou com o código {publication.rc}."
            )

        publication.wait_for_publish(
            timeout=settings.publish_timeout_seconds
        )

        if not publication.is_published():
            raise MqttPublishError(
                "O broker não confirmou a publicação dentro do tempo limite."
            )

        return str(payload.get("message_id") or "")

    except MqttError:
        raise
    except (OSError, RuntimeError, ValueError) as error:
        raise MqttPublishError(
            f"Falha na comunicação MQTT: {error}"
        ) from error
    finally:
        try:
            client.disconnect()
        except Exception:
            pass

        if loop_started:
            client.loop_stop()


def publish_measurement(
    session: Mapping[str, Any],
    measurement: Mapping[str, Any],
    settings: MqttSettings | None = None,
) -> str:
    """
    Constrói e publica uma única medição.

    Esta função não é executada automaticamente. Só envia quando for
    chamada pelos handlers "Enviar selecionado" ou "Enviar tudo".
    """

    settings = settings or MqttSettings.from_file()
    payload = build_measurement_payload(
        session=session,
        measurement=measurement,
        settings=settings,
    )
    return publish_json(payload, settings)
