# Aplicação de Caudalímetro Industrial — Protótipo Python

Este projeto é uma primeira versão funcional da aplicação para um dispositivo com ecrã e botões industriais. Foi feito em **Python + Tkinter**, sem dependências externas, para ser fácil de correr em Windows, Linux ou Raspberry Pi.

## Fluxo implementado

1. Login do operador
2. Menu principal
   - Medir caudal
   - Enviar dados
3. Identificação do molde
4. Seleção do diâmetro do circuito
5. Introdução da pressão à entrada
6. Introdução do número de circuitos por lado
7. Escolha do lado a medir
8. Medição de caudal por circuito
   - Caudal atual
   - Caudal mínimo
   - Caudal médio
   - Caudal máximo
9. Conclusão e gravação das medições
10. Envio/sincronização simulada dos dados

## Como executar

```bash
python caudalimetro_app.py
```

## Organização do código

O ficheiro principal foi dividido por responsabilidade:

- `caudalimetro_app.py` — ponto de entrada; cria e inicia a aplicação.
- `caudalimetro/app.py` — classe principal `CaudalimetroApp` e estado global da interface.
- `caudalimetro/config.py` — tamanhos, cores, opções e caminhos da pasta `data/`.
- `caudalimetro/models.py` — modelos de dados das sessões e medições.
- `caudalimetro/keyboard.py` — navegação por teclado/botões físicos.
- `caudalimetro/persistence.py` — gravação em JSON/CSV e envio simulado.
- `caudalimetro/measurement.py` — lógica de medição e simulação do caudal.
- `caudalimetro/ui_components.py` — componentes visuais reutilizáveis.
- `caudalimetro/screens.py` — ecrãs da aplicação.

## Controlos

| Tecla | Ação |
|---|---|
| ↑ / ↓ | Navegar entre campos ou opções |
| 0-9 | Introduzir valores |
| . ou , | Introduzir valor decimal |
| Enter ou # | Confirmar |
| Espaço | Selecionar |
| Backspace | Apagar último carácter |
| Delete ou * | Apagar tudo no campo atual |
| ← | Voltar |
| Esc | Sair |

## Ficheiros gerados

A aplicação cria automaticamente a pasta `data/` com:

- `data/sessoes/*.json` — uma sessão completa por ficheiro
- `data/medicoes.csv` — histórico tabular das medições
- `data/enviados/*.json` — cópia das sessões marcadas como enviadas

## Integração com sensor real

Nesta versão, o caudal é simulado no ficheiro `caudalimetro/measurement.py`, no método:

```python
def simulated_flow_sample(self) -> float:
```

Quando tiveres o sensor escolhido, a integração deve substituir esta função por uma leitura real. Por exemplo:

- contagem de impulsos via GPIO no Raspberry Pi;
- leitura através de microcontrolador por USB/Serial;
- leitura por protocolo industrial, como Modbus, caso o sensor/use gateway o suporte.

## Integração com botões físicos

A interface já está preparada para funcionar sem rato, através de teclas. Para botões físicos no Raspberry Pi, a abordagem recomendada é mapear cada botão industrial para uma ação equivalente:

- botão verde → confirmar/selecionar;
- botão vermelho → apagar/cancelar;
- botão azul → confirmar;
- setas/codificador → navegar;
- keypad numérico → introdução de valores.

Depois, a leitura GPIO pode chamar diretamente os métodos da aplicação:

```python
app.confirm()
app.go_back()
app.move(1)
app.move(-1)
app.add_char("1")
```

## Próximas melhorias recomendadas

- Criar configuração externa para diâmetros disponíveis.
- Ligar a um sensor real de caudal.
- Implementar validação de operadores/PIN numa base de dados local.
- Implementar envio real para servidor via MQTT, HTTP ou API interna.
- Adicionar modo offline com reenvio automático quando houver ligação.
- Gerar relatórios por molde, operador e data.
