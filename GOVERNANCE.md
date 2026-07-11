# Governance

MCP Builder Toolkit é um projeto open source mantido por um único mantenedor
no estágio alpha. Este documento descreve como decisões são tomadas, como
contribuições são aceitas e como o projeto evolui.

## Roles

### Maintainer

Responsável por:
- Revisar e mergear PRs
- Definir roadmap e prioridades
- Publicar releases
- Responder a issues de segurança
- Manter a constitution e os contratos públicos

No estágio alpha, o mantenedor é a única role. Novos mantenedores podem
surgir após contribuições consistentes e demonstração de entendimento do
projeto.

## Decision-making

| Tipo de decisão | Processo |
|----------------|----------|
| Bug fix | PR com teste de regressão. Revisão do mantenedor. |
| Nova feature | Issue + discussão prévia. PR com testes + docs. |
| Mudança em contrato público | ADR + spec update + migration note. |
| Mudança arquitetural | ADR + revisão do mantenedor. |
| Nova dependência runtime | Security review + justificação por escrito. |
| Release | Changelog + release notes + artifact smoke. |

## Feature acceptance criteria

Uma feature é aceita quando:
1. Resolve um problema real (não "seria legal ter")
2. Está alinhada com o roadmap
3. Não viola a constitution
4. Possui testes (unit + golden + acceptance quando aplicável)
5. Contratos públicos são atualizados se necessário
6. Documentação é atualizada

## Breaking changes

Breaking changes em contratos públicos exigem:
- ADR documentando a motivação
- Migration guide
- Uma versão de transição com deprecação
- Nova `apiVersion` no manifesto

Breaking changes em output gerado:
- Golden trees atualizados
- Release note destacando a mudança
- Comando `mcp-builder doctor` detecta projetos antigos

## Release process

1. `CHANGELOG.md` atualizado
2. Release notes em `docs/release-notes-<version>.md`
3. Tag `v<version>` criada e push
4. CI builda, assina e publica no PyPI
5. GitHub Release criado com artifacts

## Deprecation policy

Recursos deprecados são marcados com warning no `doctor` por pelo menos
uma versão minor antes de removidos. Contratos públicos seguem o ciclo
de `apiVersion`.

## Conflict resolution

Disputas técnicas são resolvidas via ADR. O mantenedor tem a palavra final
no estágio alpha.

## License

Contribuições são aceitas sob Apache 2.0.
