"""Vocabulário de material de construção / ferragens (a partir do backlog "MATERIAL OUTROS").

Acrescenta tipos de produto às categorias da biblioteca (consts.json -> libSeed) e tira termos genéricos
demais que puxavam esses itens para categorias erradas (BRANCO -> ARROZ BRANCO, ROSCA -> FARINHA ROSCA,
FERRO -> vitamina, ANEL -> bijuteria, BOMBA -> doce...). O mesmo patch vai em consts.json -> libPatch,
que o app aplica uma vez nas categorias já salvas no navegador.

Tipo sem categoria própria na biblioteca vai para MATERIAL OUTROS (categoria dinâmica: o descritivo
começa pelo próprio tipo, ex.: "RALO ...", "ARAME ...").

Uso: python3 vocab_material.py && python3 build.py
"""
import json
from pathlib import Path

here = Path(__file__).parent
PATCH_ID = 'material-2026-09'

def pl(*ws):
    """termo + plural simples da primeira palavra"""
    out = []
    for w in ws:
        out.append(w)
        head, _, rest = w.partition(' ')
        if head.endswith(('S', 'AO', 'L')) or len(head) <= 3: continue
        out.append((head + ('ES' if head.endswith(('R', 'Z')) else 'S') + ' ' + rest).strip())
    return out

PATCH = {
    'MATERIAL OUTROS': {'incluir': pl(
        'ARAME', 'TELA', 'TELA SOMBRITE', 'LONA', 'CORDA', 'CORDAO', 'CORRENTE', 'CABO DE ACO', 'FIO PARALELO', 'FIO FLEXIVEL',
        'FIO RIGIDO', 'FIO SOLIDO', 'FIO TORCIDO', 'FIO DE NYLON', 'FIO NYLON', 'FIO', 'CABO FLEXIVEL', 'CABO PP', 'CABO PARALELO',
        'SILICONE', 'SELANTE', 'VEDANTE', 'VEDA CALHA', 'VEDA TRINCA', 'VEDACALHA', 'MASSA PLASTICA', 'MASSA DE CALAFETAR',
        'PORTA', 'JANELA', 'BASCULANTE', 'VITRO', 'VENEZIANA', 'FORRO', 'CUMEEIRA', 'CALHA', 'RUFO', 'CANTONEIRA', 'PERFIL',
        'TRILHO', 'RODIZIO', 'ROLDANA', 'PUXADOR', 'TAMPA CEGA', 'TAMPA DE CAIXA', 'TAMPA CAIXA', 'TAMPA DE ESGOTO', 'PLACA CEGA',
        'PEDRA', 'PEDRA BRITA', 'PEDRA DE AFIAR', 'RATOEIRA', 'FILTRO', 'LINHA', 'LINHA DE PEDREIRO', 'LINHA PEDREIRO',
        'ACIDO MURIATICO', 'AMONIA', 'DESENGRIPANTE', 'LUBRIFICANTE', 'GRAXA', 'VASELINA', 'ESPUMA EXPANSIVA', 'ESPUMA PU',
        'CINTA', 'CINTA CATRACA', 'CANALETA', 'ELETRODUTO', 'ISOLADOR', 'CAMPAINHA', 'EMENDA', 'REGULADOR', 'REGULADOR DE GAS',
        'PROTETOR AURICULAR', 'FERRADURA', 'SACO DE ENTULHO', 'SACO RAFIA', 'LIXA', 'LIXA DAGUA', 'LIXA MASSA', 'LIXA FERRO',
        'MANTA GEOTEXTIL', 'TELHA', 'TIJOLO', 'LAJOTA', 'CAL', 'GESSO', 'VERGALHAO', 'MALHA POP', 'TRELICA', 'FECHADURA ELETRICA',
        'FERRAGEM', 'MOLA', 'ARGOLA', 'TAMPAO PVC', 'TAMPAO CEGO', 'PASSA FIO', 'RESISTENCIA', 'BOBINA', 'CORRIMAO',
        'ADAPTADOR', 'ADAPT', 'TAMPA', 'PLACA', 'TAMPAO', 'SOLEIRA', 'PINGADEIRA', 'GRADE', 'PORTAO', 'TOLDO', 'TENDA',
        'FELTRO', 'ALCA', 'PONTEIRA', 'ESCADA MARINHEIRO', 'NUMERO', 'NUMERO RESIDENCIAL', 'LETRA', 'EMPATE', 'ISCA',
        'ENCASTOADOR', 'RAQUETE', 'RAQUETE ELETRICA', 'RAQUETE MATA MOSQUITO', 'MASCARA DE SOLDA', 'MASCARA PFF2',
        'BARRA DE APOIO', 'BARRA APOIO', 'VEDA', 'SOLDA', 'SOLDA ESTANHO', 'FERRAMENTA', 'FERRAMENTAS', 'KIT FERRAMENTA',
        'OCULOS DE SEGURANCA', 'OCULOS SEGURANCA', 'OCULOS DE PROTECAO', 'OCULOS PROTECAO', 'MASSA EPOXI', 'MASSA DUREPOX',
        'MASSA DUREPOXI', 'MASSA DUREPOXE', 'MASSA ADESIVA', 'PROTETOR', 'PROTETOR DE RALO', 'PROTETOR DE QUINA', 'AGULHEIRO',
        'CAPACETE DE SEGURANCA', 'LUVA DE RASPA', 'COLETE REFLETIVO', 'CONE DE SINALIZACAO', 'FITA ZEBRADA',
    )},
    'ACESSORIO HIDRAULICA': {'incluir': pl(
        'RALO', 'RALINHO', 'GRELHA DE RALO', 'CAIXA SIFONADA', 'CAIXA DE GORDURA', 'CUBA', 'TANQUE', 'PIA', 'LAVATORIO',
        'REPARO', 'REPARO DE VALVULA', 'REPARO PARA VALVULA', 'BOIA', 'FLEXIVEL', 'ENGATE FLEXIVEL', 'VEDA TORNEIRA',
        'VALVULA', 'SIFAO', 'NIPEL', 'HIDR', 'REG', 'REGIST', 'REGISTRO ESFERA', 'BOMBA DAGUA', 'BOMBA D AGUA', 'BOMBA SUBMERSA', 'BOMBA CENTRIFUGA', 'BOMBA PERIFERICA',
        'REGULADOR DE PRESSAO', 'TORNEIRA BOIA',
    )},
    'TUBO E CONEXAO': {'incluir': pl(
        'ANEL', 'NIPLE', 'TEE', 'TE SOLD', 'TE SOLDAVEL', 'T SOLD', 'T SOLDAVEL', 'REDUCAO', 'BUCHA DE REDUCAO', 'BUCHA REDUCAO',
        'LUVA SOLDAVEL', 'LUVA SOLD', 'LUVA DE CORRER', 'LUVA PVC', 'LUVA DE REDUCAO', 'CURVA', 'UNIAO', 'ESPIGAO', 'CAP PVC',
        'ADAPTADOR SOLD', 'ADAPTADOR SOLDAVEL', 'ADAPTADOR CURTO', 'ADAPTADOR C FLANGE', 'ADAPTADOR COM FLANGE', 'ADAPTADOR FLANGE',
        'PLUG ROSCA', 'PLUG PVC', 'ANEL DE VEDACAO', 'ANEL VEDACAO', 'ANEL DE BORRACHA',
    )},
    'CONECTOR ELETRICO': {'incluir': pl(
        'PINO', 'PINO ADAPTADOR', 'PINO MACHO', 'PINO FEMEA', 'PLUG', 'PLUGUE', 'BENJAMIN', 'FILTRO DE LINHA',
        'ADAPTADOR 2P', 'ADAPTADOR 3 SAIDAS', 'ADAPTADOR UNIVERSAL', 'ADAPTADOR T', 'CONECTOR', 'CONECTOR PORCELANA',
        'CONECTOR LOUCA', 'CONECTOR DE FIO', 'CONECTOR PERFURANTE', 'CONECTOR WAGO', 'BORNE',
    )},
    'MANGUEIRA E ESGUICHO': {'incluir': pl(
        'ESGUINCHO', 'ENGATE RAPIDO', 'ENGATE', 'CONECTOR ENGATE', 'CONECTOR DE MANGUEIRA', 'CONECTOR MANGUEIRA', 'EMENDA DE MANGUEIRA',
        'EMENDA MANGUEIRA', 'ADAPTADOR MANGUEIRA', 'ADAPTADOR ENGATE', 'MANGUEIRA DE GAS', 'MANGUEIRA GAS',
    )},
    'EQUIPAMENTO MANUAL': {'incluir': pl(
        'TORQUES', 'TURQUES', 'TORQUEZ', 'TALHADEIRA', 'PONTEIRO', 'MARRETA', 'MARTELO', 'ESPATULA', 'DESEMPENADEIRA',
        'COLHER DE PEDREIRO', 'COLHER PEDREIRO', 'ARCO DE SERRA', 'ARCO SERRA', 'ARCO', 'SERRA', 'SERRA MANUAL', 'SERRINHA',
        'SERROTE', 'FOICE', 'FOICINHA', 'PICARETA', 'CAVADEIRA', 'ENXADAO', 'RASTELO', 'MACARICO', 'PISTOLA', 'PISTOLA APLICADORA',
        'REBITADOR', 'GRAMPEADOR', 'TORNO', 'TORNO DE BANCADA', 'CATRACA', 'CHAVE DE BOCA', 'CHAVE COMBINADA', 'CHAVE ESTRELA',
        'CHAVE PHILIPS', 'CHAVE DE GRIFO', 'CHAVE MANDRIL', 'CHAVE TORX', 'JOGO DE CHAVES', 'ESTILETE', 'LIMA', 'GROSA',
        'PE DE CABRA', 'CARRINHO DE MAO', 'CARRINHO MAO',
    )},
    'ACESSORIO/PECA DE REPOSICAO': {'incluir': pl(
        'BROCA', 'SERRA COPO', 'SERRA VIDEA', 'SERRA WIDIA', 'SERRA WIDEA', 'DISCO SERRA', 'DISCO DE SERRA', 'DISCO DIAMANTADO',
        'DISCO FLAP', 'ELETRODO', 'PORTA ELETRODO', 'BITS', 'PONTA PHILIPS', 'FIO DE NYLON P ROCADEIRA', 'LINHA APARAR',
        'LINHA PARA ROCADEIRA', 'CARRETEL ROCADEIRA',
    )},
    'MAQUINA ELETRICA': {'incluir': pl(
        'FERRO DE SOLDA', 'FERRO SOLDA', 'SERRA MARMORE', 'COMPRESSOR', 'ROCADEIRA', 'SOPRADOR', 'LAVADORA DE ALTA PRESSAO',
        'PISTOLA DE COLA QUENTE', 'PISTOLA COLA QUENTE', 'PISTOLA DE PINTURA', 'MAQUINA DE SOLDA',
    )},
    'MEDICAO E MARCACAO': {'incluir': pl(
        'METRO', 'METRO ARTICULADO', 'MULTIMETRO', 'ALICATE AMPERIMETRO', 'LAPIS DE CARPINTEIRO', 'LAPIS CARPINTEIRO',
        'LAPIS PARA CARPINTEIRO', 'LAPIS MARCENEIRO', 'LAPIS DE MARCENEIRO', 'GIZ DE LINHA', 'LINHA DE NIVEL',
    )},
    'TINTA E ACESSORIO': {'incluir': pl(
        'THINNER', 'AGUARRAS', 'SOLVENTE', 'ROLO DE LA', 'ROLO ESPUMA', 'ROLO DE ESPUMA', 'TRINCHA', 'MASSA CORRIDA',
        'MASSA ACRILICA', 'FUNDO PREPARADOR', 'SELATRINCA', 'ZARCAO', 'REMOVEDOR DE TINTA', 'FITA CREPE',
    )},
    'DOBRADICA E FECHADURA': {'incluir': pl('FERROLHO', 'TARJETA', 'CILINDRO', 'CILINDRO FECHADURA', 'TRINCO', 'PORTA CADEADO', 'MACANETA')},
    'FIXACAO OUTROS': {'incluir': pl('TARJETA', 'TACHINHA', 'ARRUELA LISA', 'CHUMBADOR')},
    'BUCHA E PARAFUSO': {'incluir': pl('ESCAPULA', 'BARRA ROSCADA', 'PARAFUSO SEXTAVADO', 'PORCA SEXTAVADA')},
    'ABRACADEIRA': {'incluir': pl('BRACADEIRA')},
    'PAO OUTROS TIPOS': {'excluir': ['SOLDAVEL', 'SOLD', 'PVC', 'NIPLE', 'NIPEL', 'TAMPAO', 'ADAPTADOR', 'REGISTRO', 'REGIST', 'HIDR', 'ESFERA', 'MM', 'INT', 'PLUG', 'LUVA', 'TEE', 'JOELHO', 'CONEXAO', 'AMANCO', 'TIGRE', 'KRONA', 'PRATIKO', 'VEFIX', 'BARRA ROSCADA']},
    'SALGADO CONGELADO OUTROS': {'excluir': ['LISO', 'PVC', 'SOLDAVEL', 'MM', 'ESGOTO', 'AMANCO', 'TIGRE']},
    'CEREAL EM BARRA SAUDAVEL': {'excluir': ['APOIO', 'PVC', 'INOX', 'ROSCADA', 'CM', 'MM']},
    'FITA ADESIVA OUTROS': {'incluir': pl('VEDA ROSCA', 'FITA VEDA', 'FITA VEDAROSCA', 'FITA ISOLANTE')},
    'VARAL ROUPA': {'incluir': pl('CORDA DE VARAL', 'CORDA VARAL', 'CORDA PARA VARAL', 'CORDA P VARAL', 'VARAL DE CHAO', 'VARAL DE TETO', 'KIT VARAL')},
    'ACESSORIO DE ILUMINACAO': {'incluir': pl('SOQUETE', 'SOQUETE E27', 'SOQUETE DE PORCELANA', 'BOCAL', 'RECEPTACULO')},
    'DUCHA CHUVEIRO': {'incluir': pl('RESISTENCIA PARA CHUVEIRO', 'RESISTENCIA CHUVEIRO', 'RESISTENCIA DUCHA')},
    'PISO E REVESTIMENTO': {'incluir': pl('ESPACADOR DE PISO', 'ESPACADOR PISO', 'ESPACADOR PARA PISO', 'NIVELADOR DE PISO', 'CUNHA NIVELADORA')},
    # --- termos genéricos que puxavam material para categorias erradas ---
    'ARROZ BRANCO': {'remover_incluir': ['BRANCO', 'TIPO 1']},
    'FARINHA ROSCA': {'remover_incluir': ['ROSCA'], 'incluir': ['FARINHA DE ROSCA', 'FARINHA ROSCA', 'FAR ROSCA', 'FARINHA DE PAO']},
    'VITAMINA OUTRO': {'excluir': ['LIXA', 'LIXAS', 'SOLDA', 'BRACADEIRA', 'ABRACADEIRA', 'RALO', 'CHAPA', 'VERGALHAO', 'PREGO', 'ARAME', 'SERRA', 'FERRAMENTA', 'MARTELO', 'PORTAO', 'GRADE']},
    'OUTROS SUPLEMENTOS MINERAIS': {'excluir': ['FIO', 'CABO', 'TORCIDO', 'MM', 'TUBO', 'CONEXAO', 'CHAPA', 'ARAME']},
    'BIJUTERIA': {'excluir': ['VEDACAO', 'BORRACHA', 'ESGOTO', 'FLANGE', 'ORING', 'O RING', 'PVC', 'TIGRE', 'AMANCO']},
    'LIMPADOR MULTIUSO': {'excluir': ['CORDA', 'FIO', 'PINO', 'ENGATE', 'ADAPTADOR', 'LUBRIFICANTE', 'OLEO', 'WD 40', 'WD40', 'DESENGRIPANTE', 'CAIXA', 'FERRAMENTA', 'ALICATE', 'CHAVE', 'SAIDAS']},
    'DOCE PADARIA': {'excluir': ['AGUA', 'DAGUA', 'SUBMERSA', 'PERIFERICA', 'CENTRIFUGA', 'CENTRIF', 'CV', 'BIVOLT', '127V', '220V', '110V', 'PISCINA', 'VACUO', 'COMBUSTIVEL', 'GRAXA', 'INFLAR', 'ENCHER', 'PRESSURIZADORA', 'SAPO', 'INJETORA', 'INJ', 'GALAO']},
    'AUXILIAR PARA RESPIRACAO': {'excluir': ['PISO', 'CERAMICA', 'PORCELANATO', 'NIVELADOR', 'MM', 'AZULEJO', 'REVESTIMENTO']},
    'ABSORVENTE MENSTRUAL INTERNO': {'excluir': ['PVC', 'ESGOTO', 'CEGO', 'ROSCA', 'TIGRE', 'AMANCO', 'MM', 'KRONA', 'SOLDAVEL', 'ENCART']},
    'MEIA': {'excluir': ['LAMPADA', 'E27', 'PORCELANA', 'BOCAL', 'SOQUETE E27', 'CATRACA', 'CHAVE', 'ENCAIXE', 'SEXTAVADO', 'POL']},
    'ROUPA DE CAMA': {'excluir': ['ASFALTICA', 'GEOTEXTIL', 'ALUMINIZADA', 'LIQUIDA', 'IMPERMEABILIZANTE', 'SUBCOBERTURA']},
    'SORVETE MASSA': {'excluir': ['PAZINHA', 'PAZINHAS', 'COLHER', 'COLHERES', 'DESCARTAVEL', 'PLASTICA']},
    'LAPIS/LAPISERA': {'excluir': ['CARPINTEIRO', 'MARCENEIRO', 'PEDREIRO']},
    'COLA SILICONE': {'excluir': ['SELANTE', 'ACETICO', 'NEUTRO', 'VEDACAO', 'CALAFETAR', 'BISNAGA 280G', '280G', 'TUBO 280']},
    'BICICLETA': {'excluir': ['CADEADO', 'CADEADOS']},
}
# utensílio descartável de sorvete (pazinha) -> talher descartável
PATCH['TALHER DESCARTAVEL'] = {'incluir': pl('PAZINHA', 'PAZINHA PLASTICA', 'PAZINHA DE SORVETE', 'PAZINHA P SORVETE')}


def main():
    raw = (here / 'consts.json').read_text(encoding='utf-8')
    c = json.loads(raw)
    byname = {x['nome']: x for x in c['libSeed']['categorias'] + c['cfg']['categorias']}
    faltou = [n for n in PATCH if n not in byname]
    assert not faltou, faltou
    # palavra solta (ex.: FIO, PORTA, PINO) só vale como tipo do produto, isto é, no começo da descrição ("tipo");
    # frase com mais de uma palavra entra no "incluir" normal
    for p in PATCH.values():
        inc = p.pop('incluir', [])
        p['tipo'] = [t for t in inc if ' ' not in t]
        p['incluir'] = [t for t in inc if ' ' in t]
    for nome, p in PATCH.items():
        x = byname[nome]
        x.setdefault('tipo', [])
        for k in ('incluir', 'excluir', 'tipo'):
            for t in p.get(k, []):
                if t not in x[k]: x[k].append(t)
        rm = set(p.get('remover_incluir', []))
        x['incluir'] = [t for t in x['incluir'] if t not in rm]
    c['libPatch'] = {'id': PATCH_ID, 'cats': PATCH}
    (here / 'consts.json').write_text(json.dumps(c, ensure_ascii=False), encoding='utf-8')
    print(f'{len(PATCH)} categorias ajustadas; {sum(len(p["tipo"]) for p in PATCH.values())} tipos (1a palavra) e '
          f'{sum(len(p["incluir"]) for p in PATCH.values())} frases novas')


if __name__ == '__main__':
    main()
