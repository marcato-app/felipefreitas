# Farmácia em JSON (para o AppGen)

- `farma_regras.json` (~240 KB):
  - `pipeline`: os 18 passos do algoritmo, em ordem; cada passo diz o que faz e que listas e dicionários usa;
  - `regras`: as regras do cliente com id (FAB-01, MAR-02...);
  - `constantes`: OTF, CODIGO INTERNO, STATUS...;
  - `listas`: palavras que nunca são marca ou fabricante etc.;
  - `categorias`: as 413 categorias de Farmácia, com nome oficial, código EST MER 7, início do descritivo e
    palavras de inclusão e exclusão.
- `farma_dicionarios.json` (~1,2 MB): fabricantes canônicos, siglas, códigos de laboratório, marcas Hoja/DIMA,
  princípios ativos, base de vitaminas e EST MER 7. O formato de cada um está em `formatos`.

Regenerar depois de mudar o app:
`node farma_appgen/extrai_listas.js farma_appgen/_listas.json && python3 farma_appgen/gera_json.py && rm farma_appgen/_listas.json`

Os JSON trazem as regras e os dados. O código que executa os passos (comparação de texto, nome parecido,
montagem do descritivo) continua no `src.html`. No AppGen esse motor precisa existir como função.
