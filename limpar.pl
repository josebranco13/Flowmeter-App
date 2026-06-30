#!/usr/bin/perl
use strict;
use warnings;
use File::Glob ':bsd_glob';

# 1. Definição das diretorias e ficheiros
my $dir_enviados = '/home/user/Flowmeter-App/caudalimetro_app/data/enviados';
my $ficheiro_log = '/home/user/Flowmeter-App/caudalimetro_app/data/apagados.log';

# 2. Obter dia e mês atuais (localtime é nativo do Perl e não consome recursos extra)
my ($sec, $min, $hour, $dia_atual, $mes_atual_raw, $ano_raw) = localtime();
my $mes_atual = $mes_atual_raw + 1; # No Perl, os meses vão de 0 (Jan) a 11 (Dez)

my @ficheiros = bsd_glob("$dir_enviados/*.json");
my @ficheiros_apagados;

foreach my $ficheiro (@ficheiros) {
    open my $fh, '<', $ficheiro or do {
        warn "Não foi possível abrir '$ficheiro': $!\n";
        next;
    };

    my $deve_apagar = 0;

    # Ler o ficheiro linha a linha
    while (my $linha = <$fh>) {
        # Extrair APENAS o mês e o dia (ignora o ano e as horas)
        if ($linha =~ /"enviado_em"\s*:\s*"\d{4}-(\d{2})-(\d{2})T/) {
            # O "+ 0" força a conversão para número (ex: "05" passa a 5)
            my $mes_ficheiro = $1 + 0; 
            my $dia_ficheiro = $2 + 0;

            # 3. Calcular a diferença em meses
            my $dif_meses = $mes_atual - $mes_ficheiro;
            
            # Se o valor for negativo, significa que o ficheiro é do ano passado
            # Exemplo: Atual (Fev = 2) - Ficheiro (Nov = 11) = -9. (-9 + 12 = 3 meses de diferença)
            if ($dif_meses < 0) {
                $dif_meses += 12; 
            }

            # 4. Decidir se deve apagar
            if ($dif_meses > 3) {
                $deve_apagar = 1; # Mais de 3 meses de diferença (ex: 4, 5, 6 meses)
            } elsif ($dif_meses == 3 && $dia_atual >= $dia_ficheiro) {
                $deve_apagar = 1; # Exatamente 3 meses de diferença, mas o dia atual já passou o dia do ficheiro
            }
            
            last; # Encontrámos a data, podemos parar de ler este ficheiro
        }
    }
    close $fh;

    # 5. Apagar o ficheiro
    if ($deve_apagar) {
        if (unlink $ficheiro) {
            push @ficheiros_apagados, $ficheiro;
        } else {
            warn "Não foi possível apagar '$ficheiro': $!\n";
        }
    }
}

# 6. Escrever no log
if (@ficheiros_apagados) {
    open my $log_fh, '>>', $ficheiro_log or die "Erro ao abrir o log '$ficheiro_log': $!\n";
    
    # Formatar o timestamp para o log (ex: 2026-06-29 17:30:00)
    my $timestamp_atual = sprintf("%04d-%02d-%02d %02d:%02d:%02d", $ano_raw + 1900, $mes_atual, $dia_atual, $hour, $min, $sec);
    
    print $log_fh "=== Limpeza executada a $timestamp_atual ===\n";
    foreach my $apagado (@ficheiros_apagados) {
        print $log_fh "$apagado\n";
    }
    close $log_fh;
    
    print "Sucesso: Foram apagados " . scalar(@ficheiros_apagados) . " ficheiros antigos.\n";
} else {
    print "Nenhum ficheiro para apagar com base no dia e mês.\n";
}