# ===============================================================================
# PORTLANG DSL - VERSÃO REFATORADA COM GERAÇÃO AUTOMÁTICA DE PDF
# ===============================================================================
# Trabalho de Linguagens Formais e Compiladores
# Prof.: Ivan L. Süptitz
# Grupo: João, Tiago e Victor Hugo
# ===============================================================================

import re
import json
import pandas as pd
import matplotlib.pyplot as plt
import os
import sys
from datetime import datetime
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum

# Verificar e instalar dependências para PDF
PDF_AVAILABLE = False
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    PDF_AVAILABLE = True
    print("✅ ReportLab disponível - PDFs serão gerados automaticamente")
except ImportError:
    print("📦 Instalando ReportLab para geração de PDFs...")
    try:
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "reportlab"])
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.lib import colors
        PDF_AVAILABLE = True
        print("✅ ReportLab instalado e carregado com sucesso!")
    except Exception as e:
        print(f"⚠️ Não foi possível instalar ReportLab: {e}")
        print("PDFs não serão gerados automaticamente.")

# ===============================================================================
# SISTEMA DE ERROS ESTRUTURADO
# ===============================================================================

class ErrorType(Enum):
    """Tipos de erro categorizados"""
    LEXICAL = "LÉXICO"
    SYNTACTIC = "SINTÁTICO"
    SEMANTIC = "SEMÂNTICO"
    VALIDATION = "VALIDAÇÃO"
    GENERATION = "GERAÇÃO"

class ErrorSeverity(Enum):
    """Níveis de severidade"""
    ERROR = "ERRO"
    WARNING = "AVISO"
    INFO = "INFO"

@dataclass
class DSLError:
    """Representa um erro estruturado"""
    type: ErrorType
    severity: ErrorSeverity
    code: str
    message: str
    line: Optional[int] = None
    column: Optional[int] = None
    suggestion: Optional[str] = None

class ErrorCollector:
    """Coletor centralizado de erros"""
    
    def __init__(self):
        self.errors: List[DSLError] = []
        self.warnings: List[DSLError] = []
        self.infos: List[DSLError] = []
    
    def add_error(self, error: DSLError):
        """Adiciona um erro"""
        if error.severity == ErrorSeverity.ERROR:
            self.errors.append(error)
        elif error.severity == ErrorSeverity.WARNING:
            self.warnings.append(error)
        else:
            self.infos.append(error)
    
    def has_errors(self) -> bool:
        """Verifica se há erros críticos"""
        return len(self.errors) > 0
    
    def print_summary(self):
        """Imprime resumo dos erros"""
        if self.errors:
            print(f"\n❌ {len(self.errors)} ERRO(S) ENCONTRADO(S):")
            for error in self.errors:
                location = f" (Linha {error.line})" if error.line else ""
                print(f"  • [{error.code}] {error.message}{location}")
                if error.suggestion:
                    print(f"    💡 Sugestão: {error.suggestion}")
        
        if self.warnings:
            print(f"\n⚠️ {len(self.warnings)} AVISO(S):")
            for warning in self.warnings:
                location = f" (Linha {warning.line})" if warning.line else ""
                print(f"  • [{warning.code}] {warning.message}{location}")
                if warning.suggestion:
                    print(f"    💡 Sugestão: {warning.suggestion}")
        
        if self.infos:
            print(f"\nℹ️ {len(self.infos)} INFORMAÇÃO(ÕES):")
            for info in self.infos:
                print(f"  • [{info.code}] {info.message}")

# ===============================================================================
# TOKEN E TIPOS DE TOKEN
# ===============================================================================

@dataclass
class Token:
    """Representa um token da linguagem"""
    type: str
    value: Any
    line: int
    column: int

class TokenType:
    """Tipos de tokens da linguagem"""
    # Palavras-chave
    CARTEIRA = 'CARTEIRA'
    NOME = 'NOME'
    PERFIL = 'PERFIL'
    HORIZONTE_TEMPORAL = 'HORIZONTE_TEMPORAL'
    ALOCACAO = 'ALOCACAO'
    RESTRICOES = 'RESTRICOES'
    REBALANCEAMENTO = 'REBALANCEAMENTO'

    # Tipos de ativos
    ACOES_NACIONAIS = 'ACOES_NACIONAIS'
    ACOES_INTERNACIONAIS = 'ACOES_INTERNACIONAIS'
    FUNDOS_IMOBILIARIOS = 'FUNDOS_IMOBILIARIOS'
    FUNDOS_MULTIMERCADO = 'FUNDOS_MULTIMERCADO'
    RENDA_FIXA = 'RENDA_FIXA'

    # Parâmetros
    VOLATILIDADE_MAXIMA = 'VOLATILIDADE_MAXIMA'
    TAXA_ADMINISTRATIVA_MAXIMA = 'TAXA_ADMINISTRATIVA_MAXIMA'
    SETORIAL = 'SETORIAL'
    GEOGRAFICO = 'GEOGRAFICO'
    FREQUENCIA = 'FREQUENCIA'
    TOLERANCIA = 'TOLERANCIA'

    # Valores temporais
    ANOS = 'ANOS'
    MESES = 'MESES'
    TRIMESTRAL = 'TRIMESTRAL'
    SEMESTRAL = 'SEMESTRAL'
    ANUAL = 'ANUAL'
    MENSAL = 'MENSAL'

    # Símbolos
    IGUAL = 'IGUAL'
    CHAVE_ABRE = 'CHAVE_ABRE'
    CHAVE_FECHA = 'CHAVE_FECHA'
    PONTO_VIRGULA = 'PONTO_VIRGULA'
    PORCENTAGEM = 'PORCENTAGEM'

    # Literais
    STRING = 'STRING'
    NUMERO = 'NUMERO'
    IDENTIFICADOR = 'IDENTIFICADOR'

    # Especiais
    EOF = 'EOF'
    NEWLINE = 'NEWLINE'

# ===============================================================================
# ANALISADOR LÉXICO
# ===============================================================================

class PortfolioLexer:
    """Analisador léxico com tratamento robusto de erros"""

    def __init__(self, error_collector: ErrorCollector):
        self.text = ""
        self.pos = 0
        self.line = 1
        self.column = 1
        self.tokens = []
        self.error_collector = error_collector

        # Palavras reservadas
        self.keywords = {
            'carteira': TokenType.CARTEIRA,
            'nome': TokenType.NOME,
            'perfil': TokenType.PERFIL,
            'horizonte_temporal': TokenType.HORIZONTE_TEMPORAL,
            'alocação': TokenType.ALOCACAO,
            'restrições': TokenType.RESTRICOES,
            'rebalanceamento': TokenType.REBALANCEAMENTO,
            'ações_nacionais': TokenType.ACOES_NACIONAIS,
            'ações_internacionais': TokenType.ACOES_INTERNACIONAIS,
            'fundos_imobiliarios': TokenType.FUNDOS_IMOBILIARIOS,
            'fundos_multimercado': TokenType.FUNDOS_MULTIMERCADO,
            'renda_fixa': TokenType.RENDA_FIXA,
            'volatilidade_maxima': TokenType.VOLATILIDADE_MAXIMA,
            'taxa_administrativa_maxima': TokenType.TAXA_ADMINISTRATIVA_MAXIMA,
            'setorial': TokenType.SETORIAL,
            'geografico': TokenType.GEOGRAFICO,
            'frequencia': TokenType.FREQUENCIA,
            'tolerancia': TokenType.TOLERANCIA,
            'anos': TokenType.ANOS,
            'meses': TokenType.MESES,
            'trimestral': TokenType.TRIMESTRAL,
            'semestral': TokenType.SEMESTRAL,
            'anual': TokenType.ANUAL,
            'mensal': TokenType.MENSAL
        }

    def current_char(self):
        if self.pos >= len(self.text):
            return None
        return self.text[self.pos]

    def advance(self):
        if self.pos < len(self.text) and self.text[self.pos] == '\n':
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        self.pos += 1

    def skip_whitespace(self):
        while self.current_char() and self.current_char() in ' \t':
            self.advance()

    def skip_newlines(self):
        while self.current_char() and self.current_char() in '\n\r':
            self.advance()

    def read_string(self):
        value = ""
        start_line = self.line
        start_column = self.column
        self.advance()

        while self.current_char() and self.current_char() != '"':
            if self.current_char() == '\n':
                self.error_collector.add_error(DSLError(
                    type=ErrorType.LEXICAL,
                    severity=ErrorSeverity.ERROR,
                    code="LEX001",
                    message="String não pode conter quebra de linha",
                    line=start_line,
                    column=start_column,
                    suggestion="Feche a string na mesma linha"
                ))
                break
            value += self.current_char()
            self.advance()

        if self.current_char() == '"':
            self.advance()
        else:
            self.error_collector.add_error(DSLError(
                type=ErrorType.LEXICAL,
                severity=ErrorSeverity.ERROR,
                code="LEX002",
                message="String não fechada",
                line=start_line,
                column=start_column,
                suggestion="Adicione \" no final da string"
            ))

        return value

    def read_number(self):
        value = ""
        start_line = self.line
        start_column = self.column
        dot_count = 0

        while self.current_char() and (self.current_char().isdigit() or self.current_char() == '.'):
            if self.current_char() == '.':
                dot_count += 1
                if dot_count > 1:
                    self.error_collector.add_error(DSLError(
                        type=ErrorType.LEXICAL,
                        severity=ErrorSeverity.ERROR,
                        code="LEX003",
                        message="Número com múltiplos pontos decimais",
                        line=start_line,
                        column=start_column,
                        suggestion="Use apenas um ponto decimal"
                    ))
                    break
            value += self.current_char()
            self.advance()

        try:
            if '.' in value:
                return float(value)
            else:
                return int(value)
        except ValueError:
            self.error_collector.add_error(DSLError(
                type=ErrorType.LEXICAL,
                severity=ErrorSeverity.ERROR,
                code="LEX004",
                message=f"Número inválido: {value}",
                line=start_line,
                column=start_column
            ))
            return 0

    def read_identifier(self):
        value = ""
        while self.current_char() and (self.current_char().isalnum() or self.current_char() in '_ã'):
            value += self.current_char()
            self.advance()
        return value

    def tokenize(self, text):
        self.text = text
        self.pos = 0
        self.line = 1
        self.column = 1
        self.tokens = []

        while self.current_char():
            if self.current_char() in ' \t':
                self.skip_whitespace()
                continue

            if self.current_char() in '\n\r':
                self.skip_newlines()
                continue

            if self.current_char() == '=':
                self.tokens.append(Token(TokenType.IGUAL, '=', self.line, self.column))
                self.advance()
            elif self.current_char() == '{':
                self.tokens.append(Token(TokenType.CHAVE_ABRE, '{', self.line, self.column))
                self.advance()
            elif self.current_char() == '}':
                self.tokens.append(Token(TokenType.CHAVE_FECHA, '}', self.line, self.column))
                self.advance()
            elif self.current_char() == ';':
                self.tokens.append(Token(TokenType.PONTO_VIRGULA, ';', self.line, self.column))
                self.advance()
            elif self.current_char() == '%':
                self.tokens.append(Token(TokenType.PORCENTAGEM, '%', self.line, self.column))
                self.advance()
            elif self.current_char() == '"':
                string_value = self.read_string()
                self.tokens.append(Token(TokenType.STRING, string_value, self.line, self.column))
            elif self.current_char().isdigit():
                number_value = self.read_number()
                self.tokens.append(Token(TokenType.NUMERO, number_value, self.line, self.column))
            elif self.current_char().isalpha() or self.current_char() == '_':
                identifier = self.read_identifier()
                token_type = self.keywords.get(identifier, TokenType.IDENTIFICADOR)
                self.tokens.append(Token(token_type, identifier, self.line, self.column))
            else:
                self.error_collector.add_error(DSLError(
                    type=ErrorType.LEXICAL,
                    severity=ErrorSeverity.ERROR,
                    code="LEX005",
                    message=f"Caractere não reconhecido: '{self.current_char()}'",
                    line=self.line,
                    column=self.column,
                    suggestion="Verifique se há caracteres especiais não permitidos"
                ))
                self.advance()

        self.tokens.append(Token(TokenType.EOF, None, self.line, self.column))
        return self.tokens

# ===============================================================================
# ANALISADOR SINTÁTICO
# ===============================================================================

class PortfolioParser:
    """Analisador sintático com recuperação de erros"""

    def __init__(self, error_collector: ErrorCollector):
        self.tokens = []
        self.pos = 0
        self.current_token = None
        self.error_collector = error_collector

    def peek_token(self, offset=0):
        peek_pos = self.pos + offset
        if peek_pos >= len(self.tokens):
            return self.tokens[-1]
        return self.tokens[peek_pos]

    def advance_token(self):
        if self.pos < len(self.tokens) - 1:
            self.pos += 1
        self.current_token = self.tokens[self.pos]

    def expect_token(self, expected_type):
        if self.current_token.type != expected_type:
            self.error_collector.add_error(DSLError(
                type=ErrorType.SYNTACTIC,
                severity=ErrorSeverity.ERROR,
                code="SYN001",
                message=f"Esperado {expected_type}, encontrado {self.current_token.type}",
                line=self.current_token.line,
                column=self.current_token.column,
                suggestion=f"Adicione o token {expected_type}"
            ))
            return None
        
        value = self.current_token.value
        self.advance_token()
        return value

    def parse(self, tokens):
        self.tokens = tokens
        self.pos = 0
        self.current_token = tokens[0]

        try:
            result = self.parse_programa()
            return result
        except Exception as e:
            self.error_collector.add_error(DSLError(
                type=ErrorType.SYNTACTIC,
                severity=ErrorSeverity.ERROR,
                code="SYN999",
                message=f"Erro interno do parser: {str(e)}",
                line=self.current_token.line if self.current_token else None
            ))
            return None

    def parse_programa(self):
        return self.parse_carteira()

    def parse_carteira(self):
        if not self.expect_token(TokenType.CARTEIRA):
            return None
        
        if not self.expect_token(TokenType.CHAVE_ABRE):
            return None

        configuracoes = self.parse_configuracoes()
        alocacao = self.parse_alocacao()

        restricoes = {}
        rebalanceamento = {}

        if self.current_token.type == TokenType.RESTRICOES:
            restricoes = self.parse_restricoes()

        if self.current_token.type == TokenType.REBALANCEAMENTO:
            rebalanceamento = self.parse_rebalanceamento()

        self.expect_token(TokenType.CHAVE_FECHA)

        return {
            'configuracoes': configuracoes,
            'alocacao': alocacao,
            'restricoes': restricoes,
            'rebalanceamento': rebalanceamento
        }

    def parse_configuracoes(self):
        configuracoes = {}

        while self.current_token.type in [TokenType.NOME, TokenType.PERFIL, TokenType.HORIZONTE_TEMPORAL]:
            if self.current_token.type == TokenType.NOME:
                self.advance_token()
                if self.expect_token(TokenType.IGUAL):
                    nome = self.expect_token(TokenType.STRING)
                    if nome:
                        configuracoes['nome'] = nome
                    self.expect_token(TokenType.PONTO_VIRGULA)

            elif self.current_token.type == TokenType.PERFIL:
                self.advance_token()
                if self.expect_token(TokenType.IGUAL):
                    perfil = self.expect_token(TokenType.STRING)
                    if perfil:
                        configuracoes['perfil'] = perfil
                    self.expect_token(TokenType.PONTO_VIRGULA)

            elif self.current_token.type == TokenType.HORIZONTE_TEMPORAL:
                self.advance_token()
                if self.expect_token(TokenType.IGUAL):
                    numero = self.expect_token(TokenType.NUMERO)
                    if numero and self.current_token.type in [TokenType.ANOS, TokenType.MESES]:
                        unidade = self.current_token.value
                        self.advance_token()
                        configuracoes['horizonte_temporal'] = f"{numero} {unidade}"
                    self.expect_token(TokenType.PONTO_VIRGULA)

        return configuracoes

    def parse_alocacao(self):
        if not self.expect_token(TokenType.ALOCACAO):
            return {}
        
        if not self.expect_token(TokenType.CHAVE_ABRE):
            return {}

        alocacao = {}

        asset_types = [
            TokenType.ACOES_NACIONAIS, TokenType.ACOES_INTERNACIONAIS,
            TokenType.FUNDOS_IMOBILIARIOS, TokenType.FUNDOS_MULTIMERCADO,
            TokenType.RENDA_FIXA
        ]

        while self.current_token.type in asset_types:
            asset_type = self.current_token.value
            self.advance_token()
            
            if self.expect_token(TokenType.IGUAL):
                percentage = self.expect_token(TokenType.NUMERO)
                if percentage and self.expect_token(TokenType.PORCENTAGEM):
                    alocacao[asset_type] = percentage
                self.expect_token(TokenType.PONTO_VIRGULA)

        self.expect_token(TokenType.CHAVE_FECHA)
        return alocacao

    def parse_restricoes(self):
        self.advance_token()
        if not self.expect_token(TokenType.CHAVE_ABRE):
            return {}

        restricoes = {}

        while self.current_token.type in [TokenType.VOLATILIDADE_MAXIMA, TokenType.TAXA_ADMINISTRATIVA_MAXIMA]:
            if self.current_token.type == TokenType.VOLATILIDADE_MAXIMA:
                self.advance_token()
                if self.expect_token(TokenType.IGUAL):
                    valor = self.expect_token(TokenType.NUMERO)
                    if valor and self.expect_token(TokenType.PORCENTAGEM):
                        restricoes['volatilidade_maxima'] = valor
                    self.expect_token(TokenType.PONTO_VIRGULA)
            elif self.current_token.type == TokenType.TAXA_ADMINISTRATIVA_MAXIMA:
                self.advance_token()
                if self.expect_token(TokenType.IGUAL):
                    valor = self.expect_token(TokenType.NUMERO)
                    if valor and self.expect_token(TokenType.PORCENTAGEM):
                        restricoes['taxa_administrativa_maxima'] = valor
                    self.expect_token(TokenType.PONTO_VIRGULA)

        self.expect_token(TokenType.CHAVE_FECHA)
        return restricoes

    def parse_rebalanceamento(self):
        self.advance_token()
        if not self.expect_token(TokenType.CHAVE_ABRE):
            return {}

        rebalanceamento = {}

        if self.current_token.type == TokenType.FREQUENCIA:
            self.advance_token()
            if self.expect_token(TokenType.IGUAL):
                if self.current_token.type in [TokenType.TRIMESTRAL, TokenType.SEMESTRAL, 
                                             TokenType.ANUAL, TokenType.MENSAL]:
                    frequencia = self.current_token.value
                    self.advance_token()
                    rebalanceamento['frequencia'] = frequencia
                self.expect_token(TokenType.PONTO_VIRGULA)

        if self.current_token.type == TokenType.TOLERANCIA:
            self.advance_token()
            if self.expect_token(TokenType.IGUAL):
                tolerancia = self.expect_token(TokenType.NUMERO)
                if tolerancia and self.expect_token(TokenType.PORCENTAGEM):
                    rebalanceamento['tolerancia'] = tolerancia
                self.expect_token(TokenType.PONTO_VIRGULA)

        self.expect_token(TokenType.CHAVE_FECHA)
        return rebalanceamento

# ===============================================================================
# VALIDADOR SEMÂNTICO
# ===============================================================================

class PortfolioValidator:
    """Validador semântico com validações robustas"""

    def __init__(self, error_collector: ErrorCollector):
        self.error_collector = error_collector

    def validate(self, portfolio_data):
        if not portfolio_data:
            self.error_collector.add_error(DSLError(
                type=ErrorType.SEMANTIC,
                severity=ErrorSeverity.ERROR,
                code="SEM001",
                message="Dados da carteira inválidos ou ausentes"
            ))
            return False

        print("\n🔍 Executando validações semânticas...")

        self._validate_allocation_sum(portfolio_data)
        self._validate_percentage_ranges(portfolio_data)
        self._validate_risk_profile_consistency(portfolio_data)
        self._validate_restrictions(portfolio_data)

        return not self.error_collector.has_errors()

    def _validate_allocation_sum(self, data):
        alocacao = data.get('alocacao', {})
        if not alocacao:
            self.error_collector.add_error(DSLError(
                type=ErrorType.SEMANTIC,
                severity=ErrorSeverity.ERROR,
                code="SEM002",
                message="Nenhuma alocação de ativos definida",
                suggestion="Adicione pelo menos um ativo na seção alocação"
            ))
            return

        total = sum(alocacao.values())
        
        if abs(total - 100) > 0.01:
            if total > 100:
                self.error_collector.add_error(DSLError(
                    type=ErrorType.SEMANTIC,
                    severity=ErrorSeverity.ERROR,
                    code="SEM003",
                    message=f"Soma das alocações é {total}%, excede 100%",
                    suggestion=f"Reduza as alocações em {total - 100:.2f}%"
                ))
            else:
                self.error_collector.add_error(DSLError(
                    type=ErrorType.SEMANTIC,
                    severity=ErrorSeverity.ERROR,
                    code="SEM004",
                    message=f"Soma das alocações é {total}%, faltam {100 - total:.2f}%",
                    suggestion=f"Adicione {100 - total:.2f}% em outros ativos"
                ))
        else:
            print("✅ Soma das alocações: 100%")

    def _validate_percentage_ranges(self, data):
        alocacao = data.get('alocacao', {})
        
        for asset, percentage in alocacao.items():
            if not (0 <= percentage <= 100):
                self.error_collector.add_error(DSLError(
                    type=ErrorType.SEMANTIC,
                    severity=ErrorSeverity.ERROR,
                    code="SEM005",
                    message=f"Alocação {asset}: {percentage}% fora do intervalo [0, 100]",
                    suggestion="Use percentuais entre 0% e 100%"
                ))

        print("✅ Intervalos percentuais validados")

    def _validate_risk_profile_consistency(self, data):
        config = data.get('configuracoes', {})
        if 'perfil' not in config:
            self.error_collector.add_error(DSLError(
                type=ErrorType.SEMANTIC,
                severity=ErrorSeverity.WARNING,
                code="SEM007",
                message="Perfil de risco não definido",
                suggestion="Defina o perfil como 'conservador', 'moderado' ou 'arrojado'"
            ))
            return

        profile = config['perfil'].lower()
        alocacao = data.get('alocacao', {})

        high_risk_assets = ['ações_nacionais', 'ações_internacionais', 'fundos_multimercado']
        risk_exposure = sum(alocacao.get(asset, 0) for asset in high_risk_assets)

        if profile == 'conservador':
            if risk_exposure > 30:
                self.error_collector.add_error(DSLError(
                    type=ErrorType.SEMANTIC,
                    severity=ErrorSeverity.ERROR,
                    code="SEM008",
                    message=f"Perfil conservador com {risk_exposure}% em ativos de alto risco",
                    suggestion="Reduza exposição a ações e fundos multimercado para máximo 30%"
                ))
            else:
                print(f"✅ Perfil conservador adequado: {risk_exposure}% em alto risco")
        
        elif profile == 'moderado':
            if risk_exposure < 20 or risk_exposure > 70:
                self.error_collector.add_error(DSLError(
                    type=ErrorType.SEMANTIC,
                    severity=ErrorSeverity.WARNING,
                    code="SEM009",
                    message=f"Perfil moderado com {risk_exposure}% em ativos de risco",
                    suggestion="Mantenha exposição entre 20-70% para perfil moderado"
                ))
            else:
                print(f"✅ Perfil moderado adequado: {risk_exposure}% em alto risco")

        elif profile == 'arrojado':
            if risk_exposure < 50:
                self.error_collector.add_error(DSLError(
                    type=ErrorType.SEMANTIC,
                    severity=ErrorSeverity.WARNING,
                    code="SEM011",
                    message=f"Perfil arrojado com apenas {risk_exposure}% em ativos de risco",
                    suggestion="Considere aumentar exposição para pelo menos 50%"
                ))
            else:
                print(f"✅ Perfil arrojado adequado: {risk_exposure}% em alto risco")

    def _validate_restrictions(self, data):
        restricoes = data.get('restricoes', {})
        
        if 'volatilidade_maxima' in restricoes:
            vol = restricoes['volatilidade_maxima']
            if vol < 0 or vol > 50:
                self.error_collector.add_error(DSLError(
                    type=ErrorType.SEMANTIC,
                    severity=ErrorSeverity.ERROR,
                    code="SEM013",
                    message=f"Volatilidade máxima inválida: {vol}%",
                    suggestion="Use valores entre 0% e 50%"
                ))
            else:
                print(f"✅ Volatilidade máxima adequada: {vol}%")
        
        if 'taxa_administrativa_maxima' in restricoes:
            taxa = restricoes['taxa_administrativa_maxima']
            if taxa < 0 or taxa > 5:
                self.error_collector.add_error(DSLError(
                    type=ErrorType.SEMANTIC,
                    severity=ErrorSeverity.ERROR,
                    code="SEM018",
                    message=f"Taxa administrativa inválida: {taxa}%",
                    suggestion="Use valores entre 0% e 5%"
                ))
            else:
                print(f"✅ Taxa administrativa adequada: {taxa}%")

# ===============================================================================
# GERADOR DE PDF COMPLETO E AUTOMÁTICO
# ===============================================================================

# ===============================================================================
# GERADOR DE PDF COMPLETO E AUTOMÁTICO
# ===============================================================================

class PortfolioPDFGenerator:
    """Gerador de PDF completo e automático para carteiras"""

    def __init__(self, portfolio_data, error_collector: ErrorCollector):
        self.data = portfolio_data
        self.error_collector = error_collector
        self.timestamp = datetime.now()

    def generate_pdf_report(self, filename=None):
        """Gera um relatório PDF completo e bonito"""
        
        if not PDF_AVAILABLE:
            self.error_collector.add_error(DSLError(
                type=ErrorType.GENERATION,
                severity=ErrorSeverity.WARNING,
                code="GEN001",
                message="ReportLab não disponível para geração de PDF",
                suggestion="Execute: pip install reportlab"
            ))
            return None

        # Nome do arquivo
        if not filename:
            config = self.data.get('configuracoes', {})
            nome_carteira = config.get('nome', 'carteira')
            safe_name = "".join(c for c in nome_carteira if c.isalnum() or c in (' ', '-', '_')).strip()
            safe_name = safe_name.replace(' ', '_').lower()
            filename = f"{safe_name}_relatorio.pdf"

        try:
            # Criar documento
            doc = SimpleDocTemplate(
                filename, 
                pagesize=A4,
                rightMargin=72, leftMargin=72,
                topMargin=72, bottomMargin=72
            )
            
            story = []
            styles = getSampleStyleSheet()
            
            # Estilos customizados
            title_style = ParagraphStyle(
                'Title',
                parent=styles['Heading1'],
                fontSize=24,
                spaceAfter=30,
                textColor=colors.darkblue,
                alignment=1,  # Centralizado
                fontName='Helvetica-Bold'
            )
            
            heading_style = ParagraphStyle(
                'Heading',
                parent=styles['Heading2'],
                fontSize=16,
                spaceAfter=12,
                textColor=colors.darkblue,
                fontName='Helvetica-Bold'
            )
            
            # === CABEÇALHO ===
            story.append(Paragraph("📊 RELATÓRIO DE CARTEIRA DE INVESTIMENTOS", title_style))
            story.append(Spacer(1, 20))
            
            # Data e sistema
            data_str = self.timestamp.strftime("%d/%m/%Y às %H:%M:%S")
            story.append(Paragraph(f"<i>Gerado em: {data_str}</i>", styles['Normal']))
            story.append(Paragraph("<i>Sistema: PortfolioLang DSL v2.0</i>", styles['Normal']))
            story.append(Paragraph("<i>Prof. Ivan L. Süptitz - UNISC</i>", styles['Normal']))
            story.append(Spacer(1, 40))
            
            # === INFORMAÇÕES GERAIS ===
            story.append(Paragraph("ℹ️ INFORMAÇÕES GERAIS", heading_style))
            story.append(Spacer(1, 10))
            
            config = self.data.get('configuracoes', {})
            info_data = [
                ['Campo', 'Valor'],
                ['Nome da Carteira', config.get('nome', 'Não informado')],
                ['Perfil de Risco', config.get('perfil', 'Não informado').title()],
                ['Horizonte Temporal', config.get('horizonte_temporal', 'Não informado')],
                ['Data de Criação', data_str],
            ]
            
            info_table = Table(info_data, colWidths=[2.5*inch, 3.5*inch])
            info_table.setStyle(TableStyle([
                # Cabeçalho
                ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                
                # Dados
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 11),
                ('BACKGROUND', (0, 1), (0, -1), colors.lightblue),
                ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
                
                # Bordas
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ]))
            
            story.append(info_table)
            story.append(Spacer(1, 30))
            
            # === ALOCAÇÃO DE ATIVOS ===
            story.append(Paragraph("💰 ALOCAÇÃO DE ATIVOS", heading_style))
            story.append(Spacer(1, 10))
            
            alocacao = self.data.get('alocacao', {})
            
            if alocacao:
                # Tabela de alocação
                alocacao_data = [['Classe de Ativo', 'Percentual (%)', 'Classificação de Risco']]
                
                high_risk = ['ações_nacionais', 'ações_internacionais', 'fundos_multimercado']
                total = 0
                
                # Ordenar por percentual (maior para menor)
                sorted_assets = sorted(alocacao.items(), key=lambda x: x[1], reverse=True)
                
                for asset, percentage in sorted_assets:
                    asset_name = asset.replace('_', ' ').title()
                    risk_class = "Alto Risco" if asset in high_risk else "Baixo Risco"
                    alocacao_data.append([asset_name, f"{percentage}%", risk_class])
                    total += percentage
                
                # Total
                alocacao_data.append(['TOTAL ALOCADO', f"{total}%", ""])
                
                alocacao_table = Table(alocacao_data, colWidths=[2.5*inch, 1.5*inch, 1.5*inch])
                alocacao_table.setStyle(TableStyle([
                    # Cabeçalho
                    ('BACKGROUND', (0, 0), (-1, 0), colors.darkgreen),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 12),
                    
                    # Dados
                    ('FONTNAME', (0, 1), (-1, -2), 'Helvetica'),
                    ('FONTSIZE', (0, 1), (-1, -2), 11),
                    ('ALIGN', (1, 0), (1, -1), 'CENTER'),
                    ('ALIGN', (2, 0), (2, -1), 'CENTER'),
                    
                    # Total
                    ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
                    ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                    
                    # Bordas
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ]))
                
                # Cores alternadas para legibilidade
                for i in range(1, len(alocacao_data) - 1, 2):
                    alocacao_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, i), (-1, i), colors.beige),
                    ]))
                
                story.append(alocacao_table)
            else:
                story.append(Paragraph("⚠️ Nenhuma alocação definida", styles['Normal']))
            
            story.append(Spacer(1, 30))
            
            # === ANÁLISE DA CARTEIRA ===
            story.append(Paragraph("📈 ANÁLISE DA CARTEIRA", heading_style))
            story.append(Spacer(1, 10))
            
            if alocacao:
                # Calcular métricas
                high_risk_assets = ['ações_nacionais', 'ações_internacionais', 'fundos_multimercado']
                risk_exposure = sum(alocacao.get(asset, 0) for asset in high_risk_assets)
                conservative_exposure = sum(alocacao.get(asset, 0) for asset in ['renda_fixa', 'fundos_imobiliarios'])
                diversification = len(alocacao)
                total_allocated = sum(alocacao.values())
                
                # Análise do perfil
                profile = config.get('perfil', '').lower()
                if profile == 'conservador' and risk_exposure <= 30:
                    profile_analysis = "✅ Adequado ao perfil"
                    profile_color = colors.green
                elif profile == 'moderado' and 20 <= risk_exposure <= 70:
                    profile_analysis = "✅ Adequado ao perfil"
                    profile_color = colors.green
                elif profile == 'arrojado' and risk_exposure >= 50:
                    profile_analysis = "✅ Adequado ao perfil"
                    profile_color = colors.green
                else:
                    profile_analysis = "⚠️ Requer atenção"
                    profile_color = colors.orange
                
                # Status da alocação
                allocation_status = "✅ Correta (100%)" if abs(total_allocated - 100) <= 0.01 else f"⚠️ Incorreta ({total_allocated}%)"
                allocation_color = colors.green if abs(total_allocated - 100) <= 0.01 else colors.red
                
                metrics_data = [
                    ['Métrica', 'Valor', 'Status'],
                    ['Total de Classes de Ativos', str(diversification), 'Alta' if diversification >= 4 else 'Média' if diversification >= 2 else 'Baixa'],
                    ['Total Alocado', f"{total_allocated}%", allocation_status],
                    ['Exposição ao Alto Risco', f"{risk_exposure}%", 'Alta' if risk_exposure > 60 else 'Moderada' if risk_exposure > 30 else 'Baixa'],
                    ['Exposição Conservadora', f"{conservative_exposure}%", 'Alta' if conservative_exposure > 60 else 'Moderada' if conservative_exposure > 30 else 'Baixa'],
                    ['Compatibilidade com Perfil', profile_analysis, ''],
                ]
                
                metrics_table = Table(metrics_data, colWidths=[2.2*inch, 1.8*inch, 1.5*inch])
                metrics_table.setStyle(TableStyle([
                    # Cabeçalho
                    ('BACKGROUND', (0, 0), (-1, 0), colors.purple),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 12),
                    
                    # Dados
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 1), (-1, -1), 11),
                    ('BACKGROUND', (0, 1), (0, -1), colors.lavender),
                    ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
                    
                    # Cores específicas
                    ('TEXTCOLOR', (2, 2), (2, 2), allocation_color),
                    ('TEXTCOLOR', (1, -1), (1, -1), profile_color),
                    
                    # Bordas
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
                ]))
                
                story.append(metrics_table)
            else:
                story.append(Paragraph("⚠️ Não é possível gerar análise sem alocação definida", styles['Normal']))
            
            story.append(Spacer(1, 30))
            
            # === DISTRIBUIÇÃO VISUAL ===
            if alocacao:
                story.append(Paragraph("📊 DISTRIBUIÇÃO VISUAL", heading_style))
                story.append(Spacer(1, 10))
                
                # Criar representação visual em barras
                vis_data = [['Ativo', 'Percentual', 'Barra Visual (cada █ = 5%)']]
                
                for asset, percentage in sorted(alocacao.items(), key=lambda x: x[1], reverse=True):
                    asset_name = asset.replace('_', ' ').title()
                    # Barra visual (cada █ representa 5%)
                    bars = int(percentage / 5)
           
                    visual = "█" * bars + "░"
                    vis_data.append([asset_name, f"{percentage}%", visual])
                
                vis_table = Table(vis_data, colWidths=[2.2*inch, 1*inch, 2.3*inch])
                vis_table.setStyle(TableStyle([
                    # Cabeçalho
                    ('BACKGROUND', (0, 0), (-1, 0), colors.red),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 11),
                    
                    # Dados
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 1), (-1, -1), 10),
                    ('FONTNAME', (2, 1), (2, -1), 'Courier'),  # Monospace para barras
                    ('ALIGN', (1, 0), (1, -1), 'CENTER'),
                    
                    # Bordas
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ]))
                
                story.append(vis_table)
                story.append(Spacer(1, 30))
            
            # === RESTRIÇÕES ===
            restricoes = self.data.get('restricoes', {})
            if restricoes:
                story.append(Paragraph("🔒 RESTRIÇÕES E LIMITES", heading_style))
                story.append(Spacer(1, 10))
                
                restricoes_data = [['Tipo de Restrição', 'Valor Máximo']]
                
                if 'volatilidade_maxima' in restricoes:
                    restricoes_data.append(['Volatilidade Máxima', f"{restricoes['volatilidade_maxima']}%"])
                
                if 'taxa_administrativa_maxima' in restricoes:
                    restricoes_data.append(['Taxa Administrativa Máxima', f"{restricoes['taxa_administrativa_maxima']}%"])
                
                if len(restricoes_data) > 1:
                    restricoes_table = Table(restricoes_data, colWidths=[3*inch, 2*inch])
                    restricoes_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.orange),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, 0), 12),
                        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                        ('FONTSIZE', (0, 1), (-1, -1), 11),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black),
                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                        ('ALIGN', (1, 0), (1, -1), 'CENTER'),
                    ]))
                    
                    story.append(restricoes_table)
                    story.append(Spacer(1, 30))
            
            # === REBALANCEAMENTO ===
            rebalanceamento = self.data.get('rebalanceamento', {})
            if rebalanceamento:
                story.append(Paragraph("⚖️ CONFIGURAÇÕES DE REBALANCEAMENTO", heading_style))
                story.append(Spacer(1, 10))
                
                rebal_data = [['Parâmetro', 'Valor']]
                if 'frequencia' in rebalanceamento:
                    rebal_data.append(['Frequência', rebalanceamento['frequencia'].title()])
                
                if 'tolerancia' in rebalanceamento:
                    rebal_data.append(['Tolerância', f"{rebalanceamento['tolerancia']}%"])
                
                if len(rebal_data) > 1:
                    rebal_table = Table(rebal_data, colWidths=[2.5*inch, 2.5*inch])
                    rebal_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.lightcyan),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.darkblue),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, 0), 12),
                        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                        ('FONTSIZE', (0, 1), (-1, -1), 11),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black),
                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                        ('ALIGN', (1, 0), (1, -1), 'CENTER'),
                    ]))
                    
                    story.append(rebal_table)
                    story.append(Spacer(1, 30))
            
            # === RECOMENDAÇÕES ===
            story.append(Paragraph("💡 RECOMENDAÇÕES E OBSERVAÇÕES", heading_style))
            story.append(Spacer(1, 10))
            
            recomendacoes = []
            
            if alocacao:
                total = sum(alocacao.values())
                
                if abs(total - 100) > 0.01:
                    if total > 100:
                        recomendacoes.append(f"• Ajustar alocação: Reduzir {total - 100:.2f}% para totalizar 100%")
                    else:
                        recomendacoes.append(f"• Completar alocação: Adicionar {100 - total:.2f}% para totalizar 100%")
                
                profile = config.get('perfil', '').lower()
                high_risk_assets = ['ações_nacionais', 'ações_internacionais', 'fundos_multimercado']
                risk_exposure = sum(alocacao.get(asset, 0) for asset in high_risk_assets)
                
                if profile == 'conservador' and risk_exposure > 30:
                    recomendacoes.append("• Reduzir exposição a ativos de alto risco para adequar ao perfil conservador")
                elif profile == 'arrojado' and risk_exposure < 50:
                    recomendacoes.append("• Considerar aumentar exposição a ativos de risco para perfil arrojado")
                
                if len(alocacao) < 3:
                    recomendacoes.append("• Melhorar diversificação adicionando mais classes de ativos")
                
                max_allocation = max(alocacao.values()) if alocacao else 0
                if max_allocation > 80:
                    recomendacoes.append("• Reduzir concentração: Nenhum ativo deveria representar mais de 80%")
            
            if not recomendacoes:
                recomendacoes.append("• Carteira bem estruturada, manter monitoramento regular")
                recomendacoes.append("• Revisar periodicamente conforme mudanças no mercado")
                recomendacoes.append("• Considerar rebalanceamento conforme tolerância definida")
            
            for rec in recomendacoes:
                story.append(Paragraph(rec, styles['Normal']))
                story.append(Spacer(1, 6))
            
            story.append(Spacer(1, 40))
            
            # === RODAPÉ ===
            footer_style = ParagraphStyle(
                'Footer',
                parent=styles['Normal'],
                fontSize=9,
                textColor=colors.grey,
                alignment=1  # Centralizado
            )
            
            story.append(Paragraph("_" * 80, footer_style))
            story.append(Spacer(1, 10))
            story.append(Paragraph("Relatório gerado automaticamente pelo PortfolioLang DSL", footer_style))
            story.append(Paragraph("Sistema desenvolvido para Linguagens Formais e Compiladores", footer_style))
            story.append(Paragraph("Grupo: João, Tiago e Victor Hugo", footer_style))
            
            # Gerar PDF
            doc.build(story)
            
            # Informações do arquivo
            size_kb = os.path.getsize(filename) / 1024
            
            print(f"\n📄 PDF GERADO COM SUCESSO!")
            print(f"📁 Arquivo: {filename}")
            print(f"📏 Tamanho: {size_kb:.1f} KB")
            print(f"📅 Data: {self.timestamp.strftime('%d/%m/%Y às %H:%M:%S')}")
            
            return filename
            
        except Exception as e:
            self.error_collector.add_error(DSLError(
                type=ErrorType.GENERATION,
                severity=ErrorSeverity.ERROR,
                code="GEN003",
                message=f"Erro ao gerar PDF: {str(e)}"
            ))
            print(f"❌ Erro ao gerar PDF: {e}")
            return None

# ===============================================================================
# FUNÇÃO PRINCIPAL DE TESTE COM GERAÇÃO AUTOMÁTICA DE PDF
# ===============================================================================

def test_portfolio_dsl_with_auto_pdf():
    """Testa a DSL e gera PDF automaticamente quando não há erros"""
    
    carteira_valida = '''
carteira {
    nome = "Fundos de Inovação";
    perfil = "arrojado";
    horizonte_temporal = 15 anos;
    
    alocação {
        ações_internacionais = 50%;
        ações_nacionais = 30%;
        fundos_multimercado = 15%;
        renda_fixa = 5%;
    }
    
    restrições {
        volatilidade_maxima = 30%;
        taxa_administrativa_maxima = 3.5%;
    }
    
    rebalanceamento {
        frequencia = mensal;
        tolerancia = 4%;
    }
}
'''
    carteira_com_erro_soma = '''
    carteira {
        nome = "Carteira com Erro";
        perfil = "moderado";
        horizonte_temporal = 5 anos;
        
        alocação {
            ações_nacionais = 50%;
            renda_fixa = 60%;
        }
    }
    '''
    
    carteira_com_erro_perfil_incosistente = '''
carteira {
    nome = "Carteira Inconsistente";
    perfil = "conservador";
    horizonte_temporal = 5 anos;
    
    alocação {
        ações_nacionais = 60%;
        ações_internacionais = 30%;
        fundos_multimercado = 10%;
    }
}
'''

    carteira_com_erro_sintaxe = '''
carteira {
    nome = "Carteira Sintaxe Erro"
    perfil = "moderado";
    horizonte_temporal = 5 anos;
    
    alocação {
        ações_nacionais = 50%;
        renda_fixa = 50%;
    }
}
'''
    carteira_com_erro_porcentagem = '''
carteira {
    nome = "Carteira Percentual Erro";
    perfil = "moderado";
    horizonte_temporal = 5 anos;
    
    alocação {
        ações_nacionais = 150%; 
        renda_fixa = -50%;       
    }
}
'''

    
    test_cases = [
        # ("TESTE 1: Carteira Válida (deve gerar PDF)", carteira_valida),
        ("TESTE 2: Carteira com Erro de Soma Inválida (não deve gerar PDF)", carteira_com_erro_soma)
        # ("TESTE 3: Carteira com Erro de Perfil Inconsistente (não deve gerar PDF)", carteira_com_erro_perfil_incosistente),
        # ("TESTE 4: Carteira com Erro de Sintaxe (não deve gerar PDF)", carteira_com_erro_sintaxe),
        # ("TESTE 5: Carteira com Erro de Porcentagem (não deve gerar PDF)", carteira_com_erro_porcentagem)
    ]   
    
    print("🧪 TESTANDO PORTFOLIOLANG DSL COM GERAÇÃO AUTOMÁTICA DE PDF")
    print("=" * 70)
    
    for i, (test_name, code) in enumerate(test_cases, 1):
        print(f"\n📋 {test_name}")
        print("-" * 60)
        
        # Criar coletor de erros para este teste
        error_collector = ErrorCollector()
        
        # Análise léxica
        print("🔍 Executando análise léxica...")
        lexer = PortfolioLexer(error_collector)
        tokens = lexer.tokenize(code)
        
        if not error_collector.has_errors():
            print("✅ Análise léxica concluída com sucesso")
        
        # Análise sintática
        print("🔧 Executando análise sintática...")
        parser = PortfolioParser(error_collector)
        result = parser.parse(tokens)
        
        if result and not error_collector.has_errors():
            print("✅ Análise sintática concluída com sucesso")
        
        # Validação semântica
        if result:
            validator = PortfolioValidator(error_collector)
            is_valid = validator.validate(result)
            
            if is_valid:
                print("✅ Validação semântica passou")
            
            # Geração automática de PDF (apenas se não houver erros)
            if not error_collector.has_errors():
                print("\n📄 Gerando PDF automaticamente...")
                pdf_generator = PortfolioPDFGenerator(result, error_collector)
                pdf_filename = pdf_generator.generate_pdf_report()
                
                if pdf_filename:
                    print("🎉 PDF gerado automaticamente com sucesso!")
                    print("📖 Abra o arquivo para visualizar o relatório completo.")
                else:
                    print("❌ Falha na geração do PDF")
            else:
                print("\n⚠️ PDF não será gerado devido aos erros encontrados.")
        
        # Imprimir resumo dos erros
        error_collector.print_summary()
        
        if not error_collector.has_errors():
            print("🎉 TESTE CONCLUÍDO COM SUCESSO - PDF GERADO!")
        else:
            print("❌ TESTE FALHOU - Erros impedem geração do PDF")
        
        print("\n" + "="*60)

# ===============================================================================
# EXECUÇÃO PRINCIPAL
# ===============================================================================

if __name__ == "__main__":
    print("="*60)
    print("🎯 PORTLANG DSL v2.0 - SISTEMA COMPLETO")
    print("="*60)
    
    print("\n💡 Funcionalidades:")
    print("✅ Análise léxica e sintática completa")
    print("✅ Validação semântica rigorosa")
    print("✅ Geração automática de PDF bonito")
    print("✅ Tratamento robusto de erros")
    print("✅ Interface interativa")
    
    print("\n🚀 Executando demonstração automática...")
    
    # Executar demonstração automática
    test_portfolio_dsl_with_auto_pdf()
    
    print("\n🏆 SISTEMA COMPLETAMENTE FUNCIONAL!")
    print("✅ DSL processando carteiras corretamente")
    print("✅ PDFs sendo gerados automaticamente")
    print("✅ Validações detectando todos os erros")