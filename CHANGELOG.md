# Changelog

All new releases use [Semantic Versioning](https://semver.org/) and Conventional Commit subjects. Dates refer to the tagged source release, not to any claim that a neural student has qualified new capabilities.

## [1.2.4](https://github.com/Entif-AI/Bilqis-MLX/compare/v1.2.3...v1.2.4) (2026-11-18)


### Bug Fixes

* **bamf:** use bootstrapped C03 teacher for genesis rehearsal ([#1397](https://github.com/Entif-AI/Bilqis-MLX/issues/1397)) ([71a00bb](https://github.com/Entif-AI/Bilqis-MLX/commit/71a00bb90bfc261746a5e613e68f791b8ba9ad70))

## [1.2.3](https://github.com/Entif-AI/Bilqis-MLX/compare/v1.2.2...v1.2.3) (2026-11-18)


### Bug Fixes

* **bamf:** allow external operator run custody ([#1386](https://github.com/Entif-AI/Bilqis-MLX/issues/1386)) ([7c074d0](https://github.com/Entif-AI/Bilqis-MLX/commit/7c074d05c042855e6064312d582155e3e14c6430))
* **bamf:** bootstrap staged generation-zero active grade ([#1384](https://github.com/Entif-AI/Bilqis-MLX/issues/1384)) ([162fb72](https://github.com/Entif-AI/Bilqis-MLX/commit/162fb7212ffc62a67c5e01b46265da861883fb27))
* **bamf:** bootstrap staged generation-zero grade ([8d9b1ad](https://github.com/Entif-AI/Bilqis-MLX/commit/8d9b1ad99b6acbf57631ba124785ea074aaade0f))

## [1.2.2](https://github.com/Entif-AI/Bilqis-MLX/compare/v1.2.1...v1.2.2) (2026-11-17)


### Bug Fixes

* **release:** include refactor merges in release notes ([f1f9a34](https://github.com/Entif-AI/Bilqis-MLX/commit/f1f9a34a7d4bc6fb288967c4c469494c5b47e20b))
* **release:** include refactor merges in release notes ([#1381](https://github.com/Entif-AI/Bilqis-MLX/issues/1381)) ([a8a02b3](https://github.com/Entif-AI/Bilqis-MLX/commit/a8a02b37adbe68c405d7ec8ad24d52357254ad45))


### Code Refactoring

* **bamf:** bring back elements from earlier trainer ([#1377](https://github.com/Entif-AI/Bilqis-MLX/issues/1377)) ([003e4a0](https://github.com/Entif-AI/Bilqis-MLX/commit/003e4a0cabed097a520ba2e358efe4c82bf74523))


### PR #1377 constituent commit inventory

The integration merge [`003e4a0`](https://github.com/Entif-AI/Bilqis-MLX/commit/003e4a0cabed097a520ba2e358efe4c82bf74523) introduced **178 additional commits** since the v1.2.1 release boundary: **124 ordinary commits** and **54 internal merge commits**. Release Please normally summarizes the entire integration as one merge-commit entry; this expanded inventory retains the source history without claiming that these commits were individually authored on the release PR branch. Source range: [`a6c210e..b27115b`](https://github.com/Entif-AI/Bilqis-MLX/compare/a6c210eed8d6633e8e6f769edb28392a36e341fc...b27115be5a3a444563149d4adbb12dbadf9b0096).

<details>
<summary>124 source commits (newest-first topological order)</summary>

- [`da38f0aa88`](https://github.com/Entif-AI/Bilqis-MLX/commit/da38f0aa885504add491a50af35c7e857aa81625) fix(bamf): route rehearsal failures through ErrorBus
- [`de4cfb3ec5`](https://github.com/Entif-AI/Bilqis-MLX/commit/de4cfb3ec568d937d7d0654af69197c153d3e4ba) fix(bamf): preserve legacy source materialization fixtures
- [`f68835ec83`](https://github.com/Entif-AI/Bilqis-MLX/commit/f68835ec8359426486ce84f9b42ddcbf3b7518a6) fix(bamf): honor same-capability rehearsal custody
- [`bfdf8dbbe0`](https://github.com/Entif-AI/Bilqis-MLX/commit/bfdf8dbbe06d49d525b6e5bdb69f420c52f33a90) fix(bamf): keep target source count separate from rehearsal
- [`dc531705c3`](https://github.com/Entif-AI/Bilqis-MLX/commit/dc531705c35700ade2804c7278aabc6a1b769984) refactor(bamf): isolate rehearsal integration helpers
- [`1bde06bee2`](https://github.com/Entif-AI/Bilqis-MLX/commit/1bde06bee29d31d8cee324d932625633ee6209d1) refactor(bamf): keep rehearsal under session owner
- [`7952fa6b42`](https://github.com/Entif-AI/Bilqis-MLX/commit/7952fa6b4247f41fb5c626f09c3d8692e1bf0231) feat(bamf): materialize authority-bound rehearsal rows
- [`4ea290efbf`](https://github.com/Entif-AI/Bilqis-MLX/commit/4ea290efbf5ab4cc58eff449d0ea9dc1dfdce0f8) fix(bamf): type run stop receipt failures
- [`3d9d9aed92`](https://github.com/Entif-AI/Bilqis-MLX/commit/3d9d9aed920d8b7674713ac8377bb13371ecd7ea) fix(bamf): preserve session capture compatibility
- [`8713b77994`](https://github.com/Entif-AI/Bilqis-MLX/commit/8713b77994b73dd905b6add45546e35de8c5d5e8) fix(bamf): preserve fixed-point stop cause
- [`0a36ac2c01`](https://github.com/Entif-AI/Bilqis-MLX/commit/0a36ac2c01fcc240058c43dcf7bbeef8997f213e) refactor(bamf): split normal-stop visit loop
- [`ce64649ba8`](https://github.com/Entif-AI/Bilqis-MLX/commit/ce64649ba80b7eb39cc33e37a7443c2068f580a6) fix: harden grade certification currentness
- [`52f2ce2985`](https://github.com/Entif-AI/Bilqis-MLX/commit/52f2ce2985c3ee3e2485648d723ceacdf25c8653) fix(factory): preserve weakness module import surface
- [`61bff459f3`](https://github.com/Entif-AI/Bilqis-MLX/commit/61bff459f325c5dddea4cce3405c3d8c01a1210f) fix(compat): preserve numeric provider resume across R20
- [`d3bef5a4e4`](https://github.com/Entif-AI/Bilqis-MLX/commit/d3bef5a4e4de5c93c108b7ddced1fca14e13e2a4) test(runtime): track generic dimension advancement
- [`01593729c9`](https://github.com/Entif-AI/Bilqis-MLX/commit/01593729c9e1023fb181c491f178b23fc0d6017e) feat(factory): compile provider dimension progression
- [`48033a2f04`](https://github.com/Entif-AI/Bilqis-MLX/commit/48033a2f049ce6a565de8fcd879b9080ec42b571) test(factory): refresh classified release digest
- [`3cabc3015d`](https://github.com/Entif-AI/Bilqis-MLX/commit/3cabc3015d4dd044c3f6dbd0382890e263f28d71) refactor(bamf): split structural weakness closure proof
- [`df2fc80554`](https://github.com/Entif-AI/Bilqis-MLX/commit/df2fc80554b9f1e7f140bf75f9251cdddfa8bc4d) fix(bamf): restore structural weakness replay (#1335)
- [`8ac89d48cb`](https://github.com/Entif-AI/Bilqis-MLX/commit/8ac89d48cbd6a23ece1fe479e2b798a3330431f2) feat: add BAMF grade-boundary certification
- [`9a5d1355c2`](https://github.com/Entif-AI/Bilqis-MLX/commit/9a5d1355c2514d93f4cea9e7f6fb68918e9ced33) refactor(bamf): isolate session stop bookkeeping
- [`75166b9248`](https://github.com/Entif-AI/Bilqis-MLX/commit/75166b924898ab978a1e880ccab56db67b57e1c6) fix(bamf): harden profile custody and resume integration
- [`1ce4b6c56d`](https://github.com/Entif-AI/Bilqis-MLX/commit/1ce4b6c56dc32580cccdf40d7f5c83639b723ec3) fix(bamf): restore generic neural-inert profile adoption
- [`d70d19c7a3`](https://github.com/Entif-AI/Bilqis-MLX/commit/d70d19c7a3103f5c105625be7cdbdd190d4523a3) fix(storage): type event projection guard errors
- [`cef09f40af`](https://github.com/Entif-AI/Bilqis-MLX/commit/cef09f40af6306d3186f3b91941b9f5b4c2eeece) refactor(storage): split indexed event reconciliation
- [`cfb2aa38a9`](https://github.com/Entif-AI/Bilqis-MLX/commit/cfb2aa38a925af9e79506768e97200bc30ff38c0) fix(bamf): persist rejection projection cursor
- [`63d866d40d`](https://github.com/Entif-AI/Bilqis-MLX/commit/63d866d40d5392d68db80cf4553cfc6bdfcdcf41) test(bamf): refresh lifecycle source authority fixtures
- [`04728fea61`](https://github.com/Entif-AI/Bilqis-MLX/commit/04728fea61b79329700168f13bbd75d60e7848d1) fix(bamf): persist durable native run stop receipts
- [`8346a9a4f7`](https://github.com/Entif-AI/Bilqis-MLX/commit/8346a9a4f79d75e63a6b2ac2da018ef795a1d1dc) refactor(bamf): split session retention owner
- [`e70e39492a`](https://github.com/Entif-AI/Bilqis-MLX/commit/e70e39492aa4a73647cdd896efa7e7c332b3a7d6) refactor(bamf): satisfy R06 publication quality gate
- [`0a5bda15d5`](https://github.com/Entif-AI/Bilqis-MLX/commit/0a5bda15d5315befea3b38e49c392dda85ba6174) feat(bamf): restore R06 championship lifecycle history
- [`bb10d81c84`](https://github.com/Entif-AI/Bilqis-MLX/commit/bb10d81c845c6fc3f02da30ba403e265778ccaaa) fix(bamf): register run-authority errors
- [`c08741cab6`](https://github.com/Entif-AI/Bilqis-MLX/commit/c08741cab6685509963d20f09894a24050d83848) fix(bamf): bind native run authority
- [`cab121d97e`](https://github.com/Entif-AI/Bilqis-MLX/commit/cab121d97e9c82018070be37f90c6a268e3748a1) fix(bamf): satisfy cadence error contract gate
- [`3fcfae1e3a`](https://github.com/Entif-AI/Bilqis-MLX/commit/3fcfae1e3a3c9f6e9efcb9f550d9337be8c74993) fix(bamf): tolerate boundary writer crash temp
- [`510850b1b0`](https://github.com/Entif-AI/Bilqis-MLX/commit/510850b1b06cb09ad24a9fb2f7f726a5b36a3b07) fix(bamf): seal cadence authority boundary
- [`76f470df6b`](https://github.com/Entif-AI/Bilqis-MLX/commit/76f470df6b561141e6050b0886ffd5abe64b892e) test(bamf): finish unified cadence verification
- [`7b42247010`](https://github.com/Entif-AI/Bilqis-MLX/commit/7b4224701075d0735eceb39fd625c4072d044dbf) refactor(bamf): close cadence integration gates
- [`9b7b10aa0d`](https://github.com/Entif-AI/Bilqis-MLX/commit/9b7b10aa0d8a552b802750cbd97af6bb6f3df6d4) fix(bamf): reconcile R05 with current base
- [`5fd40bddfd`](https://github.com/Entif-AI/Bilqis-MLX/commit/5fd40bddfd0c74ecf0cd5eca8be9746486a19ed5) fix(bamf): route R05 errors through control plane
- [`61b61a6f23`](https://github.com/Entif-AI/Bilqis-MLX/commit/61b61a6f23ad1d6850c2668e60e45e13fb108545) refactor(bamf): tighten R05 execution seams
- [`4e3aff8cf3`](https://github.com/Entif-AI/Bilqis-MLX/commit/4e3aff8cf3f0d939a186e1a3a69231e477efae8b) refactor(bamf): satisfy R05 structure gates
- [`209f47915b`](https://github.com/Entif-AI/Bilqis-MLX/commit/209f47915bd90bb61b12dfd9cee56586c8fc0683) feat(bamf): restore native mentor soups
- [`a9bc231c79`](https://github.com/Entif-AI/Bilqis-MLX/commit/a9bc231c79be803fe92ee702329a4a05fdae56e9) fix(bamf): harden cadence replay custody
- [`237078522d`](https://github.com/Entif-AI/Bilqis-MLX/commit/237078522d4386acd9f4849fe0a796d1cb01a9b2) feat(bamf): add active-grade recovery cadence
- [`acee431931`](https://github.com/Entif-AI/Bilqis-MLX/commit/acee431931e2dc9af7800a8b4a8cde233b3d091d) fix(bamf): restore conditional plasticity guardrails (#1331)
- [`1f40621b5a`](https://github.com/Entif-AI/Bilqis-MLX/commit/1f40621b5ab8428c4806c7f56baa3759bfd16771) chore(bamf): bind issue 1315 review PR
- [`3f8843cb3f`](https://github.com/Entif-AI/Bilqis-MLX/commit/3f8843cb3f6cbfdd7693c9dcc8f9c9bbab9f3f87) chore(bamf): mark issue 1315 ready for review
- [`e8fa0ac86a`](https://github.com/Entif-AI/Bilqis-MLX/commit/e8fa0ac86a4c1307630547cbee843d090e171cdb) fix(bamf): fail closed on priority HOW drift
- [`048bec1e6a`](https://github.com/Entif-AI/Bilqis-MLX/commit/048bec1e6aae2f46c86e64ef7704ab0f31b74034) test(bamf): split retention throughput fixture
- [`d2fd8215ae`](https://github.com/Entif-AI/Bilqis-MLX/commit/d2fd8215ae3f4e294491042c4d41c43db3ba1a9d) test(bamf): repair differential leaf fixtures
- [`159ec18232`](https://github.com/Entif-AI/Bilqis-MLX/commit/159ec18232cf1a17cf2ac9933a0eb2946c74dbd4) fix(bamf): preserve frontier error contract
- [`821ca3a205`](https://github.com/Entif-AI/Bilqis-MLX/commit/821ca3a2055fd7dd1e0caf1ff9b76d4f8de524d6) test(bamf): lock lawful priority ownership witnesses
- [`b2d323fb79`](https://github.com/Entif-AI/Bilqis-MLX/commit/b2d323fb79a5d3537d4275ecba2888224f011336) test(bamf): split priority execution coverage
- [`0fb7f39743`](https://github.com/Entif-AI/Bilqis-MLX/commit/0fb7f3974352421a1e7191d584952cba275772f4) fix(bamf): constrain priority to active grade frontier
- [`f5db930de4`](https://github.com/Entif-AI/Bilqis-MLX/commit/f5db930de416c999cdfc314dff7be3d5f22199be) chore(bamf): activate issue 1315 in lane A
- [`b35ffd9574`](https://github.com/Entif-AI/Bilqis-MLX/commit/b35ffd95741e34e7653eed4c7d3aa6bea32cc576) chore(bamf): turn in R15 for review
- [`1dfc46026f`](https://github.com/Entif-AI/Bilqis-MLX/commit/1dfc46026fcd221bbc44d25100b0ab5546ada7ab) test(bamf): reconcile R15 proofs with unified championship contracts
- [`b6dbf9a63f`](https://github.com/Entif-AI/Bilqis-MLX/commit/b6dbf9a63f2ee9c0f6d550415ca9d2df3dc49abe) fix(retention): preserve target-first rejection issuance
- [`1c80a46469`](https://github.com/Entif-AI/Bilqis-MLX/commit/1c80a46469c471918cfa1779c68550336ed340c7) fix(bamf): reconnect native capability championships (#1326)
- [`5d16326807`](https://github.com/Entif-AI/Bilqis-MLX/commit/5d16326807c76cc5fb4dc8b5b7dcd2fc60510981) fix(bamf): name retention budget width (#1330)
- [`2669070bff`](https://github.com/Entif-AI/Bilqis-MLX/commit/2669070bffb50b840f08fc3f44dc52203e720330) fix(bamf): restore stage-correct retention economics (#1330)
- [`1d190542d5`](https://github.com/Entif-AI/Bilqis-MLX/commit/1d190542d5ada24992fc8632ad3ff3114392b8e5) test(bamf): use source-valid enrichment witness row
- [`54b0d24b62`](https://github.com/Entif-AI/Bilqis-MLX/commit/54b0d24b62b02371e0f00faab6f0fb2d963b8e85) test(bamf): bind enrichment witness to delivered row count
- [`dedf563b2c`](https://github.com/Entif-AI/Bilqis-MLX/commit/dedf563b2c25219458dafd08421787277c63fd9a) test(bamf): patch enrichment authority by canonical module
- [`762910c36b`](https://github.com/Entif-AI/Bilqis-MLX/commit/762910c36baf0a5adfff36e974ff084c82792b09) test(bamf): honor Grade A draw contract in enrichment witness
- [`a903dd3ff5`](https://github.com/Entif-AI/Bilqis-MLX/commit/a903dd3ff5c17309437dadac87e999e5ea97c1d4) fix(bamf): restore truth pattern and enrichment contracts
- [`ef0fab63fc`](https://github.com/Entif-AI/Bilqis-MLX/commit/ef0fab63fc7b7b4d65026963f2a7ac6d998ac89d) refactor(retention): split target-first screen for portable hygiene
- [`d183c77208`](https://github.com/Entif-AI/Bilqis-MLX/commit/d183c772089e8178a32e804ec97cd07f5a2428e1) fix(retention): restore target-first fresh evidence for #1329
- [`8bb3c409d3`](https://github.com/Entif-AI/Bilqis-MLX/commit/8bb3c409d3629b926032ad0452a1d354d25eeb3d) chore(bamf): mark issue 1314 ready for review
- [`b255c0dc61`](https://github.com/Entif-AI/Bilqis-MLX/commit/b255c0dc613f1cd9d083597c09696bb0d1b8734c) fix(bamf): pass proposal through certification seam
- [`d8b8bbab3b`](https://github.com/Entif-AI/Bilqis-MLX/commit/d8b8bbab3bf996f1e24715da5b48dafc74503aba) fix(bamf): bind frozen grade to historical acceptance
- [`6c58964418`](https://github.com/Entif-AI/Bilqis-MLX/commit/6c589644184b39191b521d0bb3bdf9bd3652b21d) fix(bamf): harden active generated grade authority
- [`8b76330757`](https://github.com/Entif-AI/Bilqis-MLX/commit/8b7633075770362d80643092202ca57cac525292) fix(runtime): satisfy portable event strategy gate (#1319)
- [`6bd77790f0`](https://github.com/Entif-AI/Bilqis-MLX/commit/6bd77790f0e56fa2b51bc0c8f000a87561a0b9fc) fix(runtime): satisfy hosted event materialization gates (#1319)
- [`ea56bcaead`](https://github.com/Entif-AI/Bilqis-MLX/commit/ea56bcaead18b4f029bb870baa219c5f064b35d1) fix(runtime): complete event source materialization (#1319)
- [`d5e4536961`](https://github.com/Entif-AI/Bilqis-MLX/commit/d5e4536961e6fefe57992484fb3e93fef7a2662a) fix(runtime): materialize event source frames (#1319)
- [`f7bb104c69`](https://github.com/Entif-AI/Bilqis-MLX/commit/f7bb104c6901ee1e5064d833a4afe9575efa3358) fix(factory): preserve split public identity (#1319)
- [`7e5dc50bf8`](https://github.com/Entif-AI/Bilqis-MLX/commit/7e5dc50bf8db44ee0ea0300fa760666754058947) refactor(factory): split autonomy contracts (#1319)
- [`aaf821da1d`](https://github.com/Entif-AI/Bilqis-MLX/commit/aaf821da1d8187a1d576f695d733b1620a15f021) refactor(factory): split release model contracts (#1319)
- [`1b080b11e0`](https://github.com/Entif-AI/Bilqis-MLX/commit/1b080b11e0ed5be3abba21462546a0ee215d87e2) refactor(factory): satisfy portable structure for #1317
- [`262d9c8ac4`](https://github.com/Entif-AI/Bilqis-MLX/commit/262d9c8ac427d5006b5431d3b5ba1618d08db130) feat(retention): bound ordinary visit retention scope (#1317)
- [`1ece4354d6`](https://github.com/Entif-AI/Bilqis-MLX/commit/1ece4354d6ca86b98f9571cfe0ec405d6ead01ae) fix(bamf): satisfy learning health operator contracts (#1324)
- [`d643e6ee3a`](https://github.com/Entif-AI/Bilqis-MLX/commit/d643e6ee3a9759fc32adeab84f319834b98873df) fix(bamf): close learning health review gaps (#1324)
- [`eb074fc15d`](https://github.com/Entif-AI/Bilqis-MLX/commit/eb074fc15db664ceb66026935584cc628d9a6c68) refactor(bamf): keep learning history validation bounded (#1324)
- [`f24b8f0454`](https://github.com/Entif-AI/Bilqis-MLX/commit/f24b8f0454df228d0c4a7a4d5ef2e95f5a3bb6ef) fix(bamf): harden accepted learning health custody (#1324)
- [`c4ef0d8b25`](https://github.com/Entif-AI/Bilqis-MLX/commit/c4ef0d8b253ec94a1770867861afff4d69e5029b) feat(bamf): project accepted learning health observations (#1324)
- [`73d3981149`](https://github.com/Entif-AI/Bilqis-MLX/commit/73d3981149bd543096daefe0f85acf4af4322db0) docs(bamf): track R10 review PR
- [`0ca24136ae`](https://github.com/Entif-AI/Bilqis-MLX/commit/0ca24136ae21f19ee8fd633594fa423a868cd6c2) docs(bamf): reconcile R10 unified integration proof
- [`eb53732650`](https://github.com/Entif-AI/Bilqis-MLX/commit/eb5373265010b316fc84ad0f94127704a9d727e9) revert(ci): restore BAMF readiness timeout (#1316)
- [`47f252beaa`](https://github.com/Entif-AI/Bilqis-MLX/commit/47f252beaae2de81681fc26cb67b9761dcbeee20) ci(bamf): tolerate hosted macOS runner queueing (#1316)
- [`44ab33f1ae`](https://github.com/Entif-AI/Bilqis-MLX/commit/44ab33f1ae07d715b10c4ec132db3b0895cc5755) test(bamf): keep baseline operator witness within hygiene bounds (#1316)
- [`9b8575af19`](https://github.com/Entif-AI/Bilqis-MLX/commit/9b8575af197e55843e03f2647072da64aa339841) fix(bamf): establish first lawful retention baseline (#1316)
- [`eda36bb53a`](https://github.com/Entif-AI/Bilqis-MLX/commit/eda36bb53ab078a5fef01ac05dd7357155d0795c) fix(bamf): preserve CI refactor semantics (#1318)
- [`bb18455db1`](https://github.com/Entif-AI/Bilqis-MLX/commit/bb18455db1d42c39fa4437bffa7219721e0263ab) refactor(bamf): split foundation retention runtime (#1318)
- [`bdea998382`](https://github.com/Entif-AI/Bilqis-MLX/commit/bdea99838283d914f84725a489c9769b91aad956) feat(bamf): project visit evidence to mission control (#1318)
- [`7f835eab86`](https://github.com/Entif-AI/Bilqis-MLX/commit/7f835eab86b9fbf84acbf5ae8658457d0cc063cc) fix(teacher): name outcome validation contracts
- [`c0d50f05bb`](https://github.com/Entif-AI/Bilqis-MLX/commit/c0d50f05bba880f6585ed882c7a14a71c4160273) docs(bamf): record R10 review and verification
- [`59c06edac5`](https://github.com/Entif-AI/Bilqis-MLX/commit/59c06edac522e6fa0a18106bcc5bd076e556bf46) fix(teacher): credit native candidate outcomes exactly once
- [`340b9f64ab`](https://github.com/Entif-AI/Bilqis-MLX/commit/340b9f64abcbf4329977d7ea12968e413b1dcd51) refactor(teacher): split strategy breeding owners
- [`340bcee9ea`](https://github.com/Entif-AI/Bilqis-MLX/commit/340bcee9ea3fe710780b437c96bb3ac5a79cc6ce) refactor(bamf): satisfy hosted hygiene for 1314
- [`783621b70e`](https://github.com/Entif-AI/Bilqis-MLX/commit/783621b70e281a130fd243a74d5f8f747948d228) docs(bamf): turn in issue 1314 lane A
- [`46357e1752`](https://github.com/Entif-AI/Bilqis-MLX/commit/46357e175239ee303bfbf03d61534db385b34434) feat(bamf): freeze active generated grade teaching surface
- [`40741876f8`](https://github.com/Entif-AI/Bilqis-MLX/commit/40741876f85bf29bd5f98f3c1eb9426da73bd99a) chore(bamf): activate issue 1314 in lane A
- [`d3d0f2b0a5`](https://github.com/Entif-AI/Bilqis-MLX/commit/d3d0f2b0a5999cbb94f3128244e5bbcb251ee838) docs(bamf): restore issue 1320 turn-in after hosted repair
- [`d10293ed47`](https://github.com/Entif-AI/Bilqis-MLX/commit/d10293ed476b2106f00700d1f7c5ff4fe60ed33b) refactor(bamf): satisfy hosted code hygiene for 1320
- [`9e15cb9437`](https://github.com/Entif-AI/Bilqis-MLX/commit/9e15cb9437dee2cf540b90c9cb33f314d240fca2) fix(bamf): satisfy hosted structural conformance for 1320
- [`cea3e8b0bf`](https://github.com/Entif-AI/Bilqis-MLX/commit/cea3e8b0bfa9066f2878fcdce755ae9e378520d7) docs(bamf): reopen issue 1320 for hosted structure repair
- [`bfba223300`](https://github.com/Entif-AI/Bilqis-MLX/commit/bfba2233009fdb8078ed16985cfa443908054ac6) docs(bamf): turn in issue 1320 lane A
- [`5865d28941`](https://github.com/Entif-AI/Bilqis-MLX/commit/5865d28941d4ec3ea3dbb6e0b6041efaa2a8dda7) docs(bamf): record issue 1320 final review evidence
- [`e7fffed261`](https://github.com/Entif-AI/Bilqis-MLX/commit/e7fffed2616c6caf637b23fb96e7ba8a5d5605c1) fix(runtime): make generated-grade issuance crash durable
- [`f973ba5498`](https://github.com/Entif-AI/Bilqis-MLX/commit/f973ba5498a4735a170a1a2b4b09307e54a4ea4b) fix(factory): enforce proposal issuance and transfer scope
- [`50e0594005`](https://github.com/Entif-AI/Bilqis-MLX/commit/50e05940053c4f0f24892a3a938ea546b7d98b70) chore(factory): normalize generated-grade fixture
- [`ba9c7eb9c7`](https://github.com/Entif-AI/Bilqis-MLX/commit/ba9c7eb9c7292affe6b0699f7f612990e7624c7c) fix(factory): complete generated-grade coverage evidence
- [`02e0796162`](https://github.com/Entif-AI/Bilqis-MLX/commit/02e0796162112a5fc17b4b4fc04cd8b7af2fc2c6) fix(factory): bind generated-grade policy to accepted evidence
- [`0d8cc3e7c6`](https://github.com/Entif-AI/Bilqis-MLX/commit/0d8cc3e7c68283034a0e3229f4ad5763471c7630) fix(factory): preserve generated-grade issuance lineage
- [`a41a0cb784`](https://github.com/Entif-AI/Bilqis-MLX/commit/a41a0cb784474f4e5c5f89697a1d42014fc5ff99) fix(factory): close generated-grade review findings
- [`56a2669f47`](https://github.com/Entif-AI/Bilqis-MLX/commit/56a2669f47c3e7d1440cbbdaafd6a69ae901c03c) fix(factory): route generated-grade failures through error control
- [`83f287b158`](https://github.com/Entif-AI/Bilqis-MLX/commit/83f287b158e7899fdbdf646250ab36e5a9eda021) fix(factory): close generated-grade authority seams
- [`13d82d5bd4`](https://github.com/Entif-AI/Bilqis-MLX/commit/13d82d5bd451798313b8eb440db0c9646559352b) test(factory): cover generated-grade evidence updates
- [`7803497c53`](https://github.com/Entif-AI/Bilqis-MLX/commit/7803497c53280fe8d80384cf9d2c5c6cfde0920c) feat(factory): synthesize learner-relative generated grades
- [`ff7e897c3d`](https://github.com/Entif-AI/Bilqis-MLX/commit/ff7e897c3dbb3f47126cc89cb74484d6da106f86) refactor(factory): split autonomy planning compartments
- [`495278cfbc`](https://github.com/Entif-AI/Bilqis-MLX/commit/495278cfbccd17e138b4e821aa3197145d85aff2) refactor(factory): split legacy release model contracts
- [`54f1824125`](https://github.com/Entif-AI/Bilqis-MLX/commit/54f1824125aa064591d1282ec4376dd00190d12d) chore(bamf): activate issue 1320 in lane A

</details>

<details>
<summary>54 internal integration merges (newest-first topological order)</summary>

- [`b27115be5a`](https://github.com/Entif-AI/Bilqis-MLX/commit/b27115be5a3a444563149d4adbb12dbadf9b0096) Merge branch 'main' into codex/bamf-unified-base-20261028
- [`d24eab3207`](https://github.com/Entif-AI/Bilqis-MLX/commit/d24eab3207e1338d303107b20f4f978cdd6f9e38) feat(bamf): conformance R14 \| Restore fragile-preservation rehearsal and generic retention-support geometry (#1376)
- [`93e74ae4e4`](https://github.com/Entif-AI/Bilqis-MLX/commit/93e74ae4e49a195b4e7bf3d295249a756406d92f) feat(bamf): restore durable native normal-stop receipts (#1375 R01)
- [`c2473dfe8a`](https://github.com/Entif-AI/Bilqis-MLX/commit/c2473dfe8a668215a599f7ba1fa55827d6e77f07) merge: consume current BAMF unified base
- [`d45ad8a602`](https://github.com/Entif-AI/Bilqis-MLX/commit/d45ad8a602cceb55460e40edc996e0ad4c79ce94) feat(bamf): reconnect generic grade-boundary certification (#1334) (#1374)
- [`9bada0dc6e`](https://github.com/Entif-AI/Bilqis-MLX/commit/9bada0dc6e90b5ee4e1a96245c53aa37a37351c5) merge: reconcile latest BAMF unified base
- [`e482e49a61`](https://github.com/Entif-AI/Bilqis-MLX/commit/e482e49a61730f98f8756c097e98b91b3a143406) fix(bamf): restore structural weakness replay (#1335 / R13) (#1373)
- [`f8802d16a3`](https://github.com/Entif-AI/Bilqis-MLX/commit/f8802d16a30d4b40db6273b86de34208deab84e2) merge: consume current BAMF unified base
- [`8d7adbd0c3`](https://github.com/Entif-AI/Bilqis-MLX/commit/8d7adbd0c3d218ef76edec4b244577f9322970b3) fix(bamf): restore generic provider-dimension progression (#1372 R20)
- [`d8cd2dd774`](https://github.com/Entif-AI/Bilqis-MLX/commit/d8cd2dd7745aa5e0f1f7842e9c1d811f5425d288) Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/1323-durable-stop-receipt-20261117
- [`7d528ea307`](https://github.com/Entif-AI/Bilqis-MLX/commit/7d528ea30768258e69e045485c448c1a49ea9c78) fix(bamf): restore generic neural-inert profile expansion and resume (#1371)
- [`208774ab9e`](https://github.com/Entif-AI/Bilqis-MLX/commit/208774ab9ed39f28f2d05430bf3a78c15c982bc7) Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/1341-profile-expansion-resume-20261116
- [`c3dcead471`](https://github.com/Entif-AI/Bilqis-MLX/commit/c3dcead471450710697e8b28f6881406630501fb) fix(bamf): resume rejection consumers from persistent event index (#1370)
- [`3ed79d85b9`](https://github.com/Entif-AI/Bilqis-MLX/commit/3ed79d85b9070be8287be41d3caa22f14cf4246c) fix(bamf): conformance - restore active-grade MAIN/RECOVERY cadence (#1360 / R11)
- [`cd12a28952`](https://github.com/Entif-AI/Bilqis-MLX/commit/cd12a28952079fa1788c9e7213224680589901b3) Merge reviewed unified into #1333
- [`aebebbb8c5`](https://github.com/Entif-AI/Bilqis-MLX/commit/aebebbb8c5b7bce0eaf628ae0828915c2cc10cd7) fix(bamf): restore R06 championship lifecycle history (#1359)
- [`7d064702ca`](https://github.com/Entif-AI/Bilqis-MLX/commit/7d064702ca6c87b6f0f5f75df658a8973e3866df) fix(bamf): bind native runs to typed authority (#1358)
- [`fc945005e8`](https://github.com/Entif-AI/Bilqis-MLX/commit/fc945005e8e7165a53369feb640478868e3026bb) Merge remote-tracking branch 'review-source/codex/bamf-unified-base-20261028' into codex/1333-main-recovery-20261116
- [`a5a4a4fe17`](https://github.com/Entif-AI/Bilqis-MLX/commit/a5a4a4fe17582e755921610c39bc311e66ec23ab) fix(bamf): restore native R05 mentor soups (#1357)
- [`418ee306f5`](https://github.com/Entif-AI/Bilqis-MLX/commit/418ee306f5edf966004aa7cd75c4cb1df29d3400) Merge branch 'codex/bamf-unified-base-20261028' into codex/1327-soups-20261116
- [`377291f91f`](https://github.com/Entif-AI/Bilqis-MLX/commit/377291f91f2c31b0aecb81ac45ff1a26a752337f) Merge remote-tracking branch 'review-source/codex/bamf-unified-base-20261028' into codex/1327-soups-20261116
- [`1e835559fe`](https://github.com/Entif-AI/Bilqis-MLX/commit/1e835559fe8d5e5326365b5f4d73773c58398e67) fix(bamf): restore Boolean truth coverage and Factory enrichment (R15) (#1356 #1337)
- [`9176d02e0b`](https://github.com/Entif-AI/Bilqis-MLX/commit/9176d02e0b8083c6e08a0f134edce9549d92dcbb) Merge branch 'codex/bamf-unified-base-20261028' into codex/1337-truth-pattern-enrichment-20261116
- [`fdd3389213`](https://github.com/Entif-AI/Bilqis-MLX/commit/fdd3389213189c2dae93d6e1065c0732a771ac7d) fix(bamf): restore conditional plasticity and certified-surface debt guardrails (#1355 R09)
- [`5f9447eb4d`](https://github.com/Entif-AI/Bilqis-MLX/commit/5f9447eb4d154d8455494613f6e9eabb730471b5) fix(bamf): constrain priority to lawful active frontier (#1315) (#1354)
- [`d5d0cede83`](https://github.com/Entif-AI/Bilqis-MLX/commit/d5d0cede83457b5e552735a358918a9c53b0bb6c) Merge remote-tracking branch 'review-source/codex/bamf-unified-base-20261028' into codex/1315-lawful-frontier-priority-20261116
- [`30af12f017`](https://github.com/Entif-AI/Bilqis-MLX/commit/30af12f0173fb0756ef6bc1fc2e2067c8135a5de) Merge remote-tracking branch 'review-source/codex/bamf-unified-base-20261028' into codex/1315-lawful-frontier-priority-20261116
- [`df3654c42e`](https://github.com/Entif-AI/Bilqis-MLX/commit/df3654c42ec63ca85e0e72006dedbc31942af5f4) Merge remote-tracking branch 'review-source/codex/bamf-unified-base-20261028' into codex/1315-lawful-frontier-priority-20261116
- [`f4d46a38c4`](https://github.com/Entif-AI/Bilqis-MLX/commit/f4d46a38c49328d328c75674c65032bd77808ee2) Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/1337-truth-pattern-enrichment-20261116
- [`749f1f37af`](https://github.com/Entif-AI/Bilqis-MLX/commit/749f1f37af958282c545473c67b2fd2acd184352) fix(bamf): restore stage-correct retention economics (#1330 / #1353 / R08)
- [`82bb0a60ca`](https://github.com/Entif-AI/Bilqis-MLX/commit/82bb0a60ca917c1bb8aaa0248648b041b219f140) Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/1330-stage-retention-economics-20261116
- [`62d356c2ad`](https://github.com/Entif-AI/Bilqis-MLX/commit/62d356c2ad36381d894959453b7da4cc6a4edec5) fix(bamf): conformance R04 \| Restore per-capability championship title lifecycle and defense batteries (#1352)
- [`e36301a4f0`](https://github.com/Entif-AI/Bilqis-MLX/commit/e36301a4f058234a4d23a55c49aecdd023146686) Merge latest BAMF unified base into #1326 championship epoch
- [`c35058f010`](https://github.com/Entif-AI/Bilqis-MLX/commit/c35058f010481b916d5d774e10d8328c9c590a42) Merge current BAMF unified base into #1326 championship epoch
- [`f6cd2d708c`](https://github.com/Entif-AI/Bilqis-MLX/commit/f6cd2d708c8f61625b703a6433cf00a5475deeb1) fix(bamf): restore target-first fresh retention evidence (#1329 / #1351 / R07)
- [`16834466e2`](https://github.com/Entif-AI/Bilqis-MLX/commit/16834466e23471ee810db010933684e320480e61) Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/1329-target-first-retention-20261116
- [`39f46e07da`](https://github.com/Entif-AI/Bilqis-MLX/commit/39f46e07daf86ff8dba28819373820a0d67673f9) fix(bamf): staircase repair A \| Freeze active generated grade as outer teaching authority (#1349)
- [`dd3c7f8ebc`](https://github.com/Entif-AI/Bilqis-MLX/commit/dd3c7f8ebc578570608a353c72d03fe8e2c81186) Merge remote-tracking branch 'review-source/codex/bamf-unified-base-20261028' into codex/1314-active-generated-grade-20261116
- [`ca3ad4d02b`](https://github.com/Entif-AI/Bilqis-MLX/commit/ca3ad4d02b0c89f5b40c18b87a9832eb12a10768) fix(runtime): materialize event source frames (#1319) (#1350)
- [`fb38defdb8`](https://github.com/Entif-AI/Bilqis-MLX/commit/fb38defdb8a00be48313c3fce54edd25a8c147fc) chore(bamf): reconcile unified baseline (#1319)
- [`bf71eeb2b9`](https://github.com/Entif-AI/Bilqis-MLX/commit/bf71eeb2b97c8cc61072933ea98ecc09e67af781) chore(bamf): reconcile unified baseline (#1319)
- [`473d5487a4`](https://github.com/Entif-AI/Bilqis-MLX/commit/473d5487a401721737c97b83878b928ba4abfee7) chore(bamf): reconcile unified baseline (#1319)
- [`e75b2f55b0`](https://github.com/Entif-AI/Bilqis-MLX/commit/e75b2f55b005bf35fe4e53fde5338f3b4344a2cc) fix(bamf): restore exactly-once HOW outcome learning (#1332 / #1348)
- [`0ef72da9ce`](https://github.com/Entif-AI/Bilqis-MLX/commit/0ef72da9ce8a25dffc272275d5c05c29bea654ee) Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/1332-how-policy-outcomes-20261116
- [`2c575e77d4`](https://github.com/Entif-AI/Bilqis-MLX/commit/2c575e77d49fbfed956c85546a3bd102efc4b9fd) fix(bamf): bound ordinary visit retention scope (#1317 / #1347)
- [`0bb5415716`](https://github.com/Entif-AI/Bilqis-MLX/commit/0bb54157166ce80a9eded2108eeeb0cff559f545) Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/1317-retention-cadence-20261116
- [`5a780d3158`](https://github.com/Entif-AI/Bilqis-MLX/commit/5a780d3158bee0b0bfaa92bae61034f3215ae6cd) Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/1332-how-policy-outcomes-20261116
- [`c8ecaaea29`](https://github.com/Entif-AI/Bilqis-MLX/commit/c8ecaaea2999d8f97959e263c5375306e1946235) fix(bamf): restore grade-neutral learning-health diagnostics (R02: #1346)
- [`af6d0b7d99`](https://github.com/Entif-AI/Bilqis-MLX/commit/af6d0b7d99390774b43f34b69311749627ecf84a) Merge remote-tracking branch 'review-source/codex/bamf-unified-base-20261028' into codex/1324-learning-health-20261116
- [`0b72a38b50`](https://github.com/Entif-AI/Bilqis-MLX/commit/0b72a38b50a286a7a35a0b4c3339e36aec5c577a) Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/1332-how-policy-outcomes-20261116
- [`0891128bb3`](https://github.com/Entif-AI/Bilqis-MLX/commit/0891128bb330af2de44ef8c0aa0893cb4a16f6e7) fix(bamf): staircase repair A0 \| Synthesize each next grade from learned semantic topology and acquisition cost (#1345)
- [`5aa7ea5745`](https://github.com/Entif-AI/Bilqis-MLX/commit/5aa7ea574505f4210445af900742e894cb141b8e) feat(bamf): surface per-visit teaching, score, rejection, and retention timing evidence (#1318 / #1344)
- [`46f29e1ba1`](https://github.com/Entif-AI/Bilqis-MLX/commit/46f29e1ba134973fad1b2f791cef3287b905c48f) Merge branch 'codex/bamf-unified-base-20261028' into codex/1318-visit-evidence-20261116
- [`4e834f9110`](https://github.com/Entif-AI/Bilqis-MLX/commit/4e834f9110b4a4d91c89e4679f5803440bf17f54) fix(bamf): establish first lawful retention baseline (#1316 / #1343)

</details>

## [1.2.1](https://github.com/Entif-AI/Bilqis-MLX/compare/v1.2.0...v1.2.1) (2026-11-17)


### Bug Fixes

* **docs:** relocate README assets ([4ab98b9](https://github.com/Entif-AI/Bilqis-MLX/commit/4ab98b999f046a3cde4543bddff1112f3f9c0ee5))
* **docs:** relocate README assets ([#1378](https://github.com/Entif-AI/Bilqis-MLX/issues/1378)) ([4d470fa](https://github.com/Entif-AI/Bilqis-MLX/commit/4d470fa20820060142cd6dee745c4d28c6786f90))

## [1.2.0](https://github.com/Entif-AI/Bilqis-MLX/compare/v1.1.0...v1.2.0) (2026-11-16)


### Features

* **bamf:** expose live step performance [#1266](https://github.com/Entif-AI/Bilqis-MLX/issues/1266) ([8dd25e2](https://github.com/Entif-AI/Bilqis-MLX/commit/8dd25e2cff0c50b57d40b1b373c617fa5ee6b69b))
* **bamf:** issue learner-relative lawful teaching frontier ([#1291](https://github.com/Entif-AI/Bilqis-MLX/issues/1291) / [#1305](https://github.com/Entif-AI/Bilqis-MLX/issues/1305)) ([596da24](https://github.com/Entif-AI/Bilqis-MLX/commit/596da2455e4e406ffb76cccf8e2c1d5e2a73f672))
* **bamf:** issue learner-relative teaching frontier ([#1291](https://github.com/Entif-AI/Bilqis-MLX/issues/1291)) ([1853fe9](https://github.com/Entif-AI/Bilqis-MLX/commit/1853fe9eb654e374b0891cb1a751a23e61140df7))
* **bamf:** migration hardening - enforce predecessor invariant transfer ([f1a6389](https://github.com/Entif-AI/Bilqis-MLX/commit/f1a638992b83aff8622934a431d00bed081e6cb5))
* **bamf:** preserve recursive beyond-C continuation ([#1299](https://github.com/Entif-AI/Bilqis-MLX/issues/1299) / [#1312](https://github.com/Entif-AI/Bilqis-MLX/issues/1312)) ([1f077f2](https://github.com/Entif-AI/Bilqis-MLX/commit/1f077f2aaaf2c201b0105d510c7fa8463b399ccd))
* **bamf:** refresh accepted learner evidence before C07 ([f162bfa](https://github.com/Entif-AI/Bilqis-MLX/commit/f162bfaeba3f4a283734767fb87fc73297ac3a21))
* **bamf:** report semantic materialization counts ([187697d](https://github.com/Entif-AI/Bilqis-MLX/commit/187697de3bfa0941a33af3aa145ef8310d7292a6))
* **bamf:** trainer observability - inspect candidate step timing ([#1271](https://github.com/Entif-AI/Bilqis-MLX/issues/1271)) ([d84ac84](https://github.com/Entif-AI/Bilqis-MLX/commit/d84ac8439558707760449e122f773d3b930605ba))
* **mission-control:** adds Electron GUI for monitoring and managing training runs ([#1110](https://github.com/Entif-AI/Bilqis-MLX/issues/1110)) ([3ce30d6](https://github.com/Entif-AI/Bilqis-MLX/commit/3ce30d6d9b18ff02464ceca5a3159d7b665e63f4))
* **mission-control:** inspect candidate step timing ([0d34748](https://github.com/Entif-AI/Bilqis-MLX/commit/0d347484f5337b720e1e78eb34c709eae1bfde3b))
* **mission-control:** preserve Home time evidence ([936da51](https://github.com/Entif-AI/Bilqis-MLX/commit/936da51eca9ea1859a782fb63b4f08705be1454d))
* **mission-control:** redesign Engram memory workspace ([d935bbe](https://github.com/Entif-AI/Bilqis-MLX/commit/d935bbe2d18834a1bb378894dd7ca000dc002222))
* **mission-control:** redesign Engram Memory workspace ([a48ad9c](https://github.com/Entif-AI/Bilqis-MLX/commit/a48ad9c7142c0c06ee12a9497b1eef8482a322b6))
* **mission-control:** refine Atlas workspace ([4869d9a](https://github.com/Entif-AI/Bilqis-MLX/commit/4869d9a00c57b91e2f751da14403d5cf8e6cfd05))
* **mission-control:** refine Corrections UX ([3522f09](https://github.com/Entif-AI/Bilqis-MLX/commit/3522f090ff066478f52ac317df4c137a54206597))
* **mission-control:** refine Evidence usability ([bab57bd](https://github.com/Entif-AI/Bilqis-MLX/commit/bab57bdde0c86817d02c22aae65adce2ab1a3fa5))
* **mission-control:** refine Learning workspace and inspector geometry ([04c2799](https://github.com/Entif-AI/Bilqis-MLX/commit/04c27997b69c6a1f6a9eae3c6f631f1170174346))
* **mission-control:** refine Learning workspace and inspector geometry ([3050bac](https://github.com/Entif-AI/Bilqis-MLX/commit/3050bac32614a7bb4bc8cd1ad63d2ce108ce6b03))
* **mission-control:** refine Lineage usability ([5ab6e9b](https://github.com/Entif-AI/Bilqis-MLX/commit/5ab6e9beb912579ffd51b15274b4e9d5442a59ab))
* **mission-control:** refine Model workspace ([86cf01a](https://github.com/Entif-AI/Bilqis-MLX/commit/86cf01ae89296b8b750879de3e52dda562d02676))
* **mission-control:** refine Operate usability ([f1ce512](https://github.com/Entif-AI/Bilqis-MLX/commit/f1ce5126cbc2ee9145f21821119c6667aef58589))
* **mission-control:** refine shared shell usability ([d280a3e](https://github.com/Entif-AI/Bilqis-MLX/commit/d280a3e8d47efdba34e1262ffa59018d93f7c443))
* **mission-control:** refine shared shell usability ([51ed19a](https://github.com/Entif-AI/Bilqis-MLX/commit/51ed19acbf277b621b173694561dec8513a5e401))
* **mission-control:** refine SÍ SÉ SON UX ([fedb8fd](https://github.com/Entif-AI/Bilqis-MLX/commit/fedb8fd3fc59a603f359e4e087bd288f23a19f44))
* **mission-control:** refine Teacher workspace UX ([4eafdda](https://github.com/Entif-AI/Bilqis-MLX/commit/4eafdda4d5bd09ca6f64f4f5eeaf44a0d0d28532))
* **mission-control:** separate School fixture mode ([27da609](https://github.com/Entif-AI/Bilqis-MLX/commit/27da609a8d25672224e5631f1bd131a35874a345))
* **mission-control:** stream observed trainer progress ([d2815e3](https://github.com/Entif-AI/Bilqis-MLX/commit/d2815e3151013c51fe11a298157625dce1aee6f5))
* **mission-control:** stream observed trainer progress ([28f8365](https://github.com/Entif-AI/Bilqis-MLX/commit/28f8365a631ca6f166561450fb3d844caacb25a1))
* **operator:** report BAMF planning progress ([2dcfcc6](https://github.com/Entif-AI/Bilqis-MLX/commit/2dcfcc6d26651af665eff7297ee087e5b894aea8))
* reuse compiled C05 fixed-school cohorts ([47e7f75](https://github.com/Entif-AI/Bilqis-MLX/commit/47e7f750e7c61d5b70ed727b7c71bf392d41e296))


### Bug Fixes

* **bamf:** attest replay outputs after autodiff ([3995b67](https://github.com/Entif-AI/Bilqis-MLX/commit/3995b675c2b044e8fe7aecd8c8c699eaed3eae17))
* **bamf:** bind B11 to emitted source owner ([6404f24](https://github.com/Entif-AI/Bilqis-MLX/commit/6404f2403f585d857fe2bdcc55be9b686dbb72fc))
* **bamf:** bind B11 to emitted source owner ([#1290](https://github.com/Entif-AI/Bilqis-MLX/issues/1290)) ([ea4c5e3](https://github.com/Entif-AI/Bilqis-MLX/commit/ea4c5e312b01d37b9ce6ee5bde13d0dcd574f67f))
* **bamf:** bind compatible current task lowerer ([0f4017f](https://github.com/Entif-AI/Bilqis-MLX/commit/0f4017f39bccfb6c10f4edeb8a5f236ac81eea6c))
* **bamf:** bind visit-scoped accepted currentness ([df58fd5](https://github.com/Entif-AI/Bilqis-MLX/commit/df58fd5b9716950472facd490541d38d54e35862))
* **bamf:** bind visit-scoped accepted currentness ([8466064](https://github.com/Entif-AI/Bilqis-MLX/commit/8466064eed80b3ebdea4e0d79dc9b474b26acf9a))
* **bamf:** bound duplicate frontier credit ([199a38d](https://github.com/Entif-AI/Bilqis-MLX/commit/199a38dfd94d7448f1294f508b5d24127c82106d))
* **bamf:** bound frontier scope history ([1f0376b](https://github.com/Entif-AI/Bilqis-MLX/commit/1f0376b10a0c80fed45f38d357322edcb6f5d1f2))
* **bamf:** bound optimizer validation and native AdamW dispatch ([#1233](https://github.com/Entif-AI/Bilqis-MLX/issues/1233)) ([6195844](https://github.com/Entif-AI/Bilqis-MLX/commit/61958444293c92800451bec8cab9f73bc2b7c997))
* **bamf:** classify B11 authority failures correctly ([ddfef26](https://github.com/Entif-AI/Bilqis-MLX/commit/ddfef26f950e6e12853018083ecd548099448366))
* **bamf:** close atlas context multiplicity gaps ([023748b](https://github.com/Entif-AI/Bilqis-MLX/commit/023748b9b54c14f3cb772d7e6dec9a2332c4db6d))
* **bamf:** close post-merge Atlas context multiplicity gaps [#1253](https://github.com/Entif-AI/Bilqis-MLX/issues/1253) ([35a220f](https://github.com/Entif-AI/Bilqis-MLX/commit/35a220fe6a05dffb6e879facfd8c7e2156796506))
* **bamf:** close step observability gaps [#1266](https://github.com/Entif-AI/Bilqis-MLX/issues/1266) ([413abb3](https://github.com/Entif-AI/Bilqis-MLX/commit/413abb3e0e6b2d37c892c695a9387cc7b559ff98))
* **bamf:** complete post-autodiff decoder attestation ([240a985](https://github.com/Entif-AI/Bilqis-MLX/commit/240a985fe9f6f42f85ce3304565579611b78d44e))
* **bamf:** continue after rejected candidate ([ab45144](https://github.com/Entif-AI/Bilqis-MLX/commit/ab4514444ea24a592da1da4347a6d9effa31da31))
* **bamf:** continue training after candidate rejection ([4d743ec](https://github.com/Entif-AI/Bilqis-MLX/commit/4d743ecfb6a5bce75ef6e86842c83f70807c9806))
* **bamf:** define frozen source mapping width ([5fe08ce](https://github.com/Entif-AI/Bilqis-MLX/commit/5fe08ce9d7fcc9aa845d88974097b2a74ee0ac2c)), closes [#1212](https://github.com/Entif-AI/Bilqis-MLX/issues/1212)
* **bamf:** establish C05 baseline lifecycle ([#1292](https://github.com/Entif-AI/Bilqis-MLX/issues/1292) / [#1306](https://github.com/Entif-AI/Bilqis-MLX/issues/1306)) ([9e319c3](https://github.com/Entif-AI/Bilqis-MLX/commit/9e319c38efb2fc7f46571667dd379d19c62661c5))
* **bamf:** establish C05 baseline lifecycle ([#1292](https://github.com/Entif-AI/Bilqis-MLX/issues/1292)) ([606fdd9](https://github.com/Entif-AI/Bilqis-MLX/commit/606fdd95450dfabe35d0ba1349d3a59cc8d00b5b))
* **bamf:** exclude evidence-complete teaching targets ([1186703](https://github.com/Entif-AI/Bilqis-MLX/commit/1186703d39caf98d764488b73a0e44d01d957dd2))
* **bamf:** exclude unmeasured C05 regressions ([#1298](https://github.com/Entif-AI/Bilqis-MLX/issues/1298) / [#1311](https://github.com/Entif-AI/Bilqis-MLX/issues/1311)) ([89a8807](https://github.com/Entif-AI/Bilqis-MLX/commit/89a8807c96caf985d398d8866fcfc55d07652ed4))
* **bamf:** exclude unmeasured C05 regressions ([#1298](https://github.com/Entif-AI/Bilqis-MLX/issues/1298)) ([bb0c165](https://github.com/Entif-AI/Bilqis-MLX/commit/bb0c1650bb0eedd61c433070b9340ac25e4439cf))
* **bamf:** fence incremental rejection replay ([4f2fe0d](https://github.com/Entif-AI/Bilqis-MLX/commit/4f2fe0d9cf477aaedc72bceac07788dbbdba2771))
* **bamf:** filter C03 C06 through lawful frontier ([#1297](https://github.com/Entif-AI/Bilqis-MLX/issues/1297)) ([2253469](https://github.com/Entif-AI/Bilqis-MLX/commit/22534692135085676258f28f1f8ccdd319e35d52))
* **bamf:** filter C03/C06 through lawful frontier ([#1297](https://github.com/Entif-AI/Bilqis-MLX/issues/1297) / [#1310](https://github.com/Entif-AI/Bilqis-MLX/issues/1310)) ([26acbc1](https://github.com/Entif-AI/Bilqis-MLX/commit/26acbc1a74a1dbd6006ca0242a722883e7704af0))
* **bamf:** follow-up to keep optimizer witness fail-closed ([#1233](https://github.com/Entif-AI/Bilqis-MLX/issues/1233)) ([71e7c16](https://github.com/Entif-AI/Bilqis-MLX/commit/71e7c16de44ef98c42914581863e462ce39eb7d9))
* **bamf:** freeze invariant gate constants ([28051f0](https://github.com/Entif-AI/Bilqis-MLX/commit/28051f072ad5f58b75a27e9d328692da12c312d0))
* **bamf:** harden batched evidence crash semantics [#1239](https://github.com/Entif-AI/Bilqis-MLX/issues/1239) ([f2268af](https://github.com/Entif-AI/Bilqis-MLX/commit/f2268af3ccc04212ed6370cda0a3c48e7931cf68))
* **bamf:** harden exact B11 row-owner authority ([#1294](https://github.com/Entif-AI/Bilqis-MLX/issues/1294)) ([7348642](https://github.com/Entif-AI/Bilqis-MLX/commit/7348642cb2db2f6c8f54e84dfdd8cc22fccb4293))
* **bamf:** harden exact B11 row-owner authority ([#1307](https://github.com/Entif-AI/Bilqis-MLX/issues/1307)) ([20f5836](https://github.com/Entif-AI/Bilqis-MLX/commit/20f5836e17cdbc2c1f50b29590d8abcd9f0f615d))
* **bamf:** import split motif owners directly [#1264](https://github.com/Entif-AI/Bilqis-MLX/issues/1264) ([18655dd](https://github.com/Entif-AI/Bilqis-MLX/commit/18655dd65c5c80d29abc38ee7fb028b54100ecd2))
* **bamf:** keep identity guard portable without mlx [#1238](https://github.com/Entif-AI/Bilqis-MLX/issues/1238) ([9dca524](https://github.com/Entif-AI/Bilqis-MLX/commit/9dca5247d223e47eeff71454610e2a2c398043f6))
* **bamf:** make authority failures and unmeasured evidence operator-truthful ([#1308](https://github.com/Entif-AI/Bilqis-MLX/issues/1308)) ([00a402d](https://github.com/Entif-AI/Bilqis-MLX/commit/00a402d28e822b5a3d0dcdc459f907604fe3207d))
* **bamf:** move forensic attestation out of autodiff [#1228](https://github.com/Entif-AI/Bilqis-MLX/issues/1228) ([01fe03b](https://github.com/Entif-AI/Bilqis-MLX/commit/01fe03b2de6217a62c9b3ce98251270da23f2e69))
* **bamf:** name B11 feature-row guard geometry [#1264](https://github.com/Entif-AI/Bilqis-MLX/issues/1264) ([f879f7b](https://github.com/Entif-AI/Bilqis-MLX/commit/f879f7b84965ae8919bea497203ede5c8b6ec0be))
* **bamf:** name frozen mapping entry width ([5d30eef](https://github.com/Entif-AI/Bilqis-MLX/commit/5d30eef3104aa201140c295ab2586a3968d59ad7))
* **bamf:** name trace rank contract ([b043bab](https://github.com/Entif-AI/Bilqis-MLX/commit/b043baba8af1079401d183d225988a00e30456e7))
* **bamf:** pad retained motif microbatch rows ([f0b3011](https://github.com/Entif-AI/Bilqis-MLX/commit/f0b3011f4eb0b1225d6f9506fc9c91d2383e112a))
* **bamf:** pad retained motif microbatch rows ([117b0b1](https://github.com/Entif-AI/Bilqis-MLX/commit/117b0b19ee9f41721960f836c98863418bda3e61)), closes [#1224](https://github.com/Entif-AI/Bilqis-MLX/issues/1224)
* **bamf:** pass prepared adapter to B11 authority bind [#1264](https://github.com/Entif-AI/Bilqis-MLX/issues/1264) ([a7261f7](https://github.com/Entif-AI/Bilqis-MLX/commit/a7261f74146a8d9a0d686194507a1a30dbb2fd70))
* **bamf:** preserve accepted evidence source draw ([b2e799e](https://github.com/Entif-AI/Bilqis-MLX/commit/b2e799e56b9de85e55790d2bc15c39370d3fec42))
* **bamf:** preserve C03 bootstrap across C07 adoption ([d2c20c4](https://github.com/Entif-AI/Bilqis-MLX/commit/d2c20c452ad29ca1d337dc17ea3a7f4da079e638))
* **bamf:** preserve compact frontier credit semantics ([0db0a97](https://github.com/Entif-AI/Bilqis-MLX/commit/0db0a976e7fe6529fbaf4e61525f208b22fd8f5e))
* **bamf:** preserve factory solver structure budget ([b679501](https://github.com/Entif-AI/Bilqis-MLX/commit/b67950134d97fd5760da15557859ead44a9e1dcf))
* **bamf:** preserve inference-conditioned gradients after [#1228](https://github.com/Entif-AI/Bilqis-MLX/issues/1228) ([9075780](https://github.com/Entif-AI/Bilqis-MLX/commit/9075780009ca36dfbda566653085ee4605bfa9d4))
* **bamf:** preserve inference-conditioned training gradients ([4d2bee2](https://github.com/Entif-AI/Bilqis-MLX/commit/4d2bee28dbf0227824f5dde464c8d6c199f300fb))
* **bamf:** preserve operator authority and measurement distinctions ([8da4a02](https://github.com/Entif-AI/Bilqis-MLX/commit/8da4a0281d5e4987252423de2b71d9d877c780b4))
* **bamf:** preserve packet authority error contract ([d5bada1](https://github.com/Entif-AI/Bilqis-MLX/commit/d5bada1f4e653dd4f07764b5f63f53a03826848a))
* **bamf:** preserve repeated rejection pressure ([7e7f009](https://github.com/Entif-AI/Bilqis-MLX/commit/7e7f009ac64b0bcdedbb2150e61643cb9f7c0977))
* **bamf:** preserve source packet container types ([41e43d6](https://github.com/Entif-AI/Bilqis-MLX/commit/41e43d688e4c5ecd163b1c0931396c93f843c02d))
* **bamf:** preserve source packet container types ([6e28fee](https://github.com/Entif-AI/Bilqis-MLX/commit/6e28feee4747a5c2b8a760195a20b9a8278e2da2)), closes [#1221](https://github.com/Entif-AI/Bilqis-MLX/issues/1221)
* **bamf:** re-enter C07 after accepted visits ([#1293](https://github.com/Entif-AI/Bilqis-MLX/issues/1293) / [#1309](https://github.com/Entif-AI/Bilqis-MLX/issues/1309)) ([b6c5848](https://github.com/Entif-AI/Bilqis-MLX/commit/b6c58483c6795e0e8a0bc4c7875117c79428fed7))
* **bamf:** re-enter C07 after accepted visits [#1293](https://github.com/Entif-AI/Bilqis-MLX/issues/1293) ([bf469b4](https://github.com/Entif-AI/Bilqis-MLX/commit/bf469b44d1315fd9fe64d69e62a8a18a7528a9ae))
* **bamf:** rebind post-autodiff execution identity [#1265](https://github.com/Entif-AI/Bilqis-MLX/issues/1265) ([d897de1](https://github.com/Entif-AI/Bilqis-MLX/commit/d897de19925cf20cff29f40591292bbb4565bfa4))
* **bamf:** recheck dataplane custody in currentness witness ([d51ea89](https://github.com/Entif-AI/Bilqis-MLX/commit/d51ea893e0906f4fb27de54302b9ee426ff72bd4))
* **bamf:** reconcile candidate identity telemetry after base refresh [#1238](https://github.com/Entif-AI/Bilqis-MLX/issues/1238) ([0627741](https://github.com/Entif-AI/Bilqis-MLX/commit/062774131d4825ea1ac2e808d7c55c5050061ec6))
* **bamf:** reject ambiguous legacy rejection order ([c582daf](https://github.com/Entif-AI/Bilqis-MLX/commit/c582daf97dbb12db66dc5e65a0195293131acede))
* **bamf:** repair post-autodiff execution identity regression ([#1270](https://github.com/Entif-AI/Bilqis-MLX/issues/1270)) ([3658240](https://github.com/Entif-AI/Bilqis-MLX/commit/365824052479fd880d337a67e85f5f8b55111781))
* **bamf:** replay accepted event graph sequentially ([e1ef8c7](https://github.com/Entif-AI/Bilqis-MLX/commit/e1ef8c73b71b84382b8e1a4c308903a28b9502bd))
* **bamf:** reset championship epochs and harden retention ([#1281](https://github.com/Entif-AI/Bilqis-MLX/issues/1281)) ([bc4ce56](https://github.com/Entif-AI/Bilqis-MLX/commit/bc4ce56f4ff79c4e121ea5ba61b9ee92333aa125))
* **bamf:** restore multi-step retention horizons ([5652854](https://github.com/Entif-AI/Bilqis-MLX/commit/5652854beae9acc7e4c942bdd2a249fdf47a4a95))
* **bamf:** restore source drift validation order [#1264](https://github.com/Entif-AI/Bilqis-MLX/issues/1264) ([74a6af4](https://github.com/Entif-AI/Bilqis-MLX/commit/74a6af403e0d5306963259a03131eed8d88eeef5))
* **bamf:** resume legacy rejection journals safely ([4a05ad4](https://github.com/Entif-AI/Bilqis-MLX/commit/4a05ad43a9736733fbacdbef2676570782be7d47))
* **bamf:** resume legacy rejection journals safely ([#1257](https://github.com/Entif-AI/Bilqis-MLX/issues/1257)) ([50a3f0d](https://github.com/Entif-AI/Bilqis-MLX/commit/50a3f0d7b5c09eeaa82c01ab1e496ebb71f10098))
* **bamf:** retain all frontier credit contexts ([ddc86c6](https://github.com/Entif-AI/Bilqis-MLX/commit/ddc86c62d42cc0f3574effa7141079ee2af4bfe2))
* **bamf:** retain source authority in receipt replay [#1264](https://github.com/Entif-AI/Bilqis-MLX/issues/1264) ([1b8a0e2](https://github.com/Entif-AI/Bilqis-MLX/commit/1b8a0e2803b5397e04fad5d2e9997d70369d5b2a))
* **bamf:** retention authority and reset championship epochs ([#1275](https://github.com/Entif-AI/Bilqis-MLX/issues/1275)) ([c39a33b](https://github.com/Entif-AI/Bilqis-MLX/commit/c39a33b99128dfcb846fbba18a6ebad9f724eb4e))
* **bamf:** reuse content-addressed compiled fixed-school cohorts (C05) ([bb3785a](https://github.com/Entif-AI/Bilqis-MLX/commit/bb3785a98f1523bab0b91ed0b9988f0ec5bf7a6c))
* **bamf:** reuse immutable source preparation across visit ([8ca89a5](https://github.com/Entif-AI/Bilqis-MLX/commit/8ca89a58e9815b422c297dc1681f755c661eff7c))
* **bamf:** reuse immutable source preparation across visit ([#1258](https://github.com/Entif-AI/Bilqis-MLX/issues/1258)) ([cb598cb](https://github.com/Entif-AI/Bilqis-MLX/commit/cb598cb3a9ba80b001ec2646a62f76f8e6cd8610))
* **bamf:** satisfy C05 operator contract audit ([#1298](https://github.com/Entif-AI/Bilqis-MLX/issues/1298)) ([a6a72f5](https://github.com/Entif-AI/Bilqis-MLX/commit/a6a72f589ebac2ee930250d7aff84467066e0442))
* **bamf:** satisfy identity guard quality contracts [#1238](https://github.com/Entif-AI/Bilqis-MLX/issues/1238) ([274ba8f](https://github.com/Entif-AI/Bilqis-MLX/commit/274ba8f98533fc4068930949ae592e6740f6e3bc))
* **bamf:** satisfy observation hygiene guard [#1265](https://github.com/Entif-AI/Bilqis-MLX/issues/1265) ([e6dbd86](https://github.com/Entif-AI/Bilqis-MLX/commit/e6dbd86829532aedd1afb1c2d432d8e64d3a5be7))
* **bamf:** satisfy portable C08 verification [#1236](https://github.com/Entif-AI/Bilqis-MLX/issues/1236) ([3607c9c](https://github.com/Entif-AI/Bilqis-MLX/commit/3607c9cc5255aaaaea5c216c111bed3d211ccd0e))
* **bamf:** satisfy source packet error contracts ([5571a20](https://github.com/Entif-AI/Bilqis-MLX/commit/5571a20632ee976283f632c89198a98cf9a9f681))
* **bamf:** separate priority and teaching option identity [#1261](https://github.com/Entif-AI/Bilqis-MLX/issues/1261) ([505fabc](https://github.com/Entif-AI/Bilqis-MLX/commit/505fabc11f6a755fc6226122ca2932326f299b43))
* **bamf:** separate priority and teaching option identity [#1261](https://github.com/Entif-AI/Bilqis-MLX/issues/1261) ([#1263](https://github.com/Entif-AI/Bilqis-MLX/issues/1263)) ([366e589](https://github.com/Entif-AI/Bilqis-MLX/commit/366e5895b9668ee6598c4045a57be952a1bb1659))
* **bamf:** the path of the righteous man is beset on all sides by the inequities of the selfish and the tyranny of evil men. ([ab477f7](https://github.com/Entif-AI/Bilqis-MLX/commit/ab477f7651bef81aa133ddefbfa04f054cac4246))
* **bamf:** thread prepared adapter into B11 authority bind [#1264](https://github.com/Entif-AI/Bilqis-MLX/issues/1264) ([01ff8d4](https://github.com/Entif-AI/Bilqis-MLX/commit/01ff8d4458ca9a7dd5da37f114973d85fdb3edda))
* **bamf:** throughput | reuse authenticated publication state (B13) ([d154ba3](https://github.com/Entif-AI/Bilqis-MLX/commit/d154ba38cd5cdb5173bebd30e84bedf4ba3b4c70))
* **bamf:** use canonical digest length constant ([73c2765](https://github.com/Entif-AI/Bilqis-MLX/commit/73c2765d3f88054989bc758254929abe9e1c23db))
* **bamf:** validate optimizer parent at consumption ([74d38f9](https://github.com/Entif-AI/Bilqis-MLX/commit/74d38f9ad4302a9443333f23e9ee0c5adcbc59d8))
* **ci:** follow relocated retention policy ([2f88201](https://github.com/Entif-AI/Bilqis-MLX/commit/2f8820124161153c28a5791542173f29bd1900f8))
* **ci:** name batching contract guards ([64e096d](https://github.com/Entif-AI/Bilqis-MLX/commit/64e096d378621106e4a6b99784afc92c9a6fe975))
* **ci:** refresh error control plane inventory ([fd33fe6](https://github.com/Entif-AI/Bilqis-MLX/commit/fd33fe601bab89fdc758f03d5fa16d6f42188e8e))
* **ci:** remove opaque B11 guard debt ([#1272](https://github.com/Entif-AI/Bilqis-MLX/issues/1272)) ([e2d8d2b](https://github.com/Entif-AI/Bilqis-MLX/commit/e2d8d2b273ca6e96a06ef80e65734cb3f50ee4f5))
* **ci:** satisfy portable hygiene contracts ([4c5a56d](https://github.com/Entif-AI/Bilqis-MLX/commit/4c5a56d2789f9a848ef0ddd9807559b1749080f2))
* **control-plane:** type active endpoint errors ([55c4b5b](https://github.com/Entif-AI/Bilqis-MLX/commit/55c4b5bc94fc86be9305b640579947ececb674ee))
* **mission-control:** attach to active trainer automatically ([68b8e69](https://github.com/Entif-AI/Bilqis-MLX/commit/68b8e69f768d0b151b953d116ab89ab50e225111))
* **mission-control:** classify CP01 request failures ([324c99c](https://github.com/Entif-AI/Bilqis-MLX/commit/324c99ccfd00d0ca9176e37bed27cf216e4d2012))
* **mission-control:** close School fixture boundary ([f332157](https://github.com/Entif-AI/Bilqis-MLX/commit/f332157d6ca182bb5b7869ca088aaa4e654facf6))
* **mission-control:** define frozen source mapping width ([5e21784](https://github.com/Entif-AI/Bilqis-MLX/commit/5e2178452e320b893fa3a554b518e10b160d7981))
* **mission-control:** distinguish provisional Home state ([c2d3a81](https://github.com/Entif-AI/Bilqis-MLX/commit/c2d3a817628677c7fa62a16e1bb1d9b68a3c1065))
* **mission-control:** enforce launch-owned fixture custody ([3f74f73](https://github.com/Entif-AI/Bilqis-MLX/commit/3f74f73334478114289769f909326fee9250303e))
* **mission-control:** finish Home shared usability integration ([24d512a](https://github.com/Entif-AI/Bilqis-MLX/commit/24d512a9d8d1a6ef458ecf2af23fc41fc1b4f0e3))
* **mission-control:** finish School UX integration ([ec52830](https://github.com/Entif-AI/Bilqis-MLX/commit/ec52830ad8f2f07a20043b6b9ab500ab85508d1a))
* **mission-control:** keep generation coordinates out of time ([e9d2a52](https://github.com/Entif-AI/Bilqis-MLX/commit/e9d2a52e8e7ed85c5236ad773faab2988e4efbe8))
* **mission-control:** keep Home within workstation height ([97149f4](https://github.com/Entif-AI/Bilqis-MLX/commit/97149f423733a3284a33d6cbac22bc5c4b5e1259))
* **mission-control:** keep responsive inspector out of grid flow ([6a9a066](https://github.com/Entif-AI/Bilqis-MLX/commit/6a9a066dc65c226ce379dca9466505ccdf097f42))
* **mission-control:** localize inspector evidence and refresh visual proof ([2b87206](https://github.com/Entif-AI/Bilqis-MLX/commit/2b872060014486c705e9d4fb8e24c1101bf597fb))
* **mission-control:** name telemetry bounds and keep failures nonfatal ([65d4356](https://github.com/Entif-AI/Bilqis-MLX/commit/65d4356f012d5c2410c835ecb9c366f8769d4985))
* **mission-control:** normalize observation time and durations ([c0fbcc1](https://github.com/Entif-AI/Bilqis-MLX/commit/c0fbcc193f7472b509e36beb136d10b77fd37513))
* **mission-control:** normalize observation time and durations ([4eea9f1](https://github.com/Entif-AI/Bilqis-MLX/commit/4eea9f1e37a2014ea251c6fd1e35d0d30321a040))
* **mission-control:** preserve home disclosure state ([0f6baff](https://github.com/Entif-AI/Bilqis-MLX/commit/0f6baffed55399d0c42bbb1baf197a35173e2227))
* **mission-control:** preserve home disclosure state ([42da1f3](https://github.com/Entif-AI/Bilqis-MLX/commit/42da1f38b63968ee80d5dafb63d6b54ffab195cb)), closes [#1216](https://github.com/Entif-AI/Bilqis-MLX/issues/1216)
* **mission-control:** preserve live trainer telemetry ([7d2ff8c](https://github.com/Entif-AI/Bilqis-MLX/commit/7d2ff8c8fdb8278606d901e346a8dc5e7b3bcb6f))
* **mission-control:** preserve live trainer telemetry ([#1283](https://github.com/Entif-AI/Bilqis-MLX/issues/1283)) ([1a9509b](https://github.com/Entif-AI/Bilqis-MLX/commit/1a9509b541ebdc27749995a4dc173487d0c93dc8))
* **mission-control:** recover activation teardown failures ([34e1b40](https://github.com/Entif-AI/Bilqis-MLX/commit/34e1b404664359da37689d4861e3f739be30e8db))
* **mission-control:** refine capability explorer usability ([edbfec2](https://github.com/Entif-AI/Bilqis-MLX/commit/edbfec25860d086c510b7bed92ef8d4a049564ba))
* **mission-control:** refine Capability Explorer usability ([a833d87](https://github.com/Entif-AI/Bilqis-MLX/commit/a833d8762f30ad76b2dcee6e81b1fd984eeb85ca))
* **mission-control:** repair Teacher CI integration ([0fc84b1](https://github.com/Entif-AI/Bilqis-MLX/commit/0fc84b126931124aa585c5aad61c7c2f0320ccc8))
* **mission-control:** resolution for fractional time displayed ([670f7aa](https://github.com/Entif-AI/Bilqis-MLX/commit/670f7aa4891af8cc0e9caed514c44bc6b3c1ab6b))
* **mission-control:** separate fixture launch mode ([f61d52f](https://github.com/Entif-AI/Bilqis-MLX/commit/f61d52fb1aaa1e468160dc71c777b25e8aee7359))
* **mission-control:** serialize subscription teardown ([8db9e0e](https://github.com/Entif-AI/Bilqis-MLX/commit/8db9e0e4e27ff8d40431a72ee0c8c0149a851626))
* **mission-control:** stop same-context query churn and classify safe CP01 failures ([41b4c65](https://github.com/Entif-AI/Bilqis-MLX/commit/41b4c6584c86804d803de448eba5dd8041381f0d))
* **mission-control:** synchronize inspector breakpoint modality ([ad4989c](https://github.com/Entif-AI/Bilqis-MLX/commit/ad4989cecc35f7bbadd7ab21c4e33c35579f7fd8))
* **mission-control:** use stable Model journey hooks ([bc738e5](https://github.com/Entif-AI/Bilqis-MLX/commit/bc738e5eac160acfd1027022ef1d6033b000002b))
* **planner:** validate acceptance before registrar issuance ([77fdbb6](https://github.com/Entif-AI/Bilqis-MLX/commit/77fdbb63026d46ef8a791d07bf67a6f677128509))
* reset championship epochs and harden retention ([d3bbb71](https://github.com/Entif-AI/Bilqis-MLX/commit/d3bbb71ba497aa93aa8cf922af821bcb60515717))
* **retention:** compose evaluation batching with compiled cohorts ([703deaf](https://github.com/Entif-AI/Bilqis-MLX/commit/703deafb4a3df09dcf7c27e811f1b3409658091c))
* **retention:** migrate legacy extensions to raw identity ([597b23a](https://github.com/Entif-AI/Bilqis-MLX/commit/597b23a7223fdd751dca9ed262c637f122e6bf4b))
* **runtime:** scope parent assessment reuse ([6e0b380](https://github.com/Entif-AI/Bilqis-MLX/commit/6e0b38042495d2a6132bfc1aaa0b9d9eec491620))
* **test:** call renamed pre-neural journey helper ([57b53d7](https://github.com/Entif-AI/Bilqis-MLX/commit/57b53d760e3ea526f60b126ca4c011d3528af3ac))


### Performance Improvements

* add calibrated retention canaries ([08e2561](https://github.com/Entif-AI/Bilqis-MLX/commit/08e2561fc9baf32ad4e3b516c05e810955b7784d))
* **bamf:** add calibrated reject-only retention canaries ([#1285](https://github.com/Entif-AI/Bilqis-MLX/issues/1285)) ([304a4a6](https://github.com/Entif-AI/Bilqis-MLX/commit/304a4a6e04eac7f1851426a9d2251a5e8498aa5e))
* **bamf:** batch C16.3 candidate evidence durability [#1239](https://github.com/Entif-AI/Bilqis-MLX/issues/1239) ([6607c3c](https://github.com/Entif-AI/Bilqis-MLX/commit/6607c3c386d70566e7938a5c08b8439165af63f1))
* **bamf:** batch C16.3 candidate evidence durability [#1239](https://github.com/Entif-AI/Bilqis-MLX/issues/1239) ([#1259](https://github.com/Entif-AI/Bilqis-MLX/issues/1259)) ([5e6512d](https://github.com/Entif-AI/Bilqis-MLX/commit/5e6512d3be4dd6436a300d4ea17ab70152b1760c))
* **bamf:** bind AdamW row authority to masks ([52e2971](https://github.com/Entif-AI/Bilqis-MLX/commit/52e29714ef6450ee529e7747ff9dc1ab8af93c0e))
* **bamf:** bind AdamW row authority to participation masks ([#1282](https://github.com/Entif-AI/Bilqis-MLX/issues/1282) [#1276](https://github.com/Entif-AI/Bilqis-MLX/issues/1276)) ([36a5811](https://github.com/Entif-AI/Bilqis-MLX/commit/36a581157b58ef3064abffb37a07b3345db71b34))
* **bamf:** bind B11 source authority once [#1264](https://github.com/Entif-AI/Bilqis-MLX/issues/1264) ([4bd4fbe](https://github.com/Entif-AI/Bilqis-MLX/commit/4bd4fbed701ec77e284fce4b41cbbe70714cafe7))
* **bamf:** bind execution generation per state ([c1eb0c6](https://github.com/Entif-AI/Bilqis-MLX/commit/c1eb0c609f73709545d3990907fd2a66a509e155))
* **bamf:** bind generation once per gradient dispatch ([84d701d](https://github.com/Entif-AI/Bilqis-MLX/commit/84d701df003206e86f1e3e1dc1a0d79b670ec1a5))
* **bamf:** bind immutable candidate identity core [#1238](https://github.com/Entif-AI/Bilqis-MLX/issues/1238) ([009302b](https://github.com/Entif-AI/Bilqis-MLX/commit/009302b3c010b72859a689ebd77e7a363c6fc76a))
* **bamf:** bind immutable candidate identity once ([#1238](https://github.com/Entif-AI/Bilqis-MLX/issues/1238)) ([#1260](https://github.com/Entif-AI/Bilqis-MLX/issues/1260)) ([9f4de20](https://github.com/Entif-AI/Bilqis-MLX/commit/9f4de204beb445b7199a8571da3f6bd3dc03956a))
* **bamf:** bind prequalified motif factors to B11 rows [#1264](https://github.com/Entif-AI/Bilqis-MLX/issues/1264) ([72d69b4](https://github.com/Entif-AI/Bilqis-MLX/commit/72d69b4474c39d236cad962551b32080a163d27f))
* **bamf:** bind prequalified source authority to training row [#1264](https://github.com/Entif-AI/Bilqis-MLX/issues/1264) ([7123bb6](https://github.com/Entif-AI/Bilqis-MLX/commit/7123bb687f4ad68638398001fcba4ecb6cb55d3e))
* **bamf:** bind reused feature rows to qualified projection [#1264](https://github.com/Entif-AI/Bilqis-MLX/issues/1264) ([e32b5cf](https://github.com/Entif-AI/Bilqis-MLX/commit/e32b5cff84923eb59f83bf470488cdb3e4bb1055))
* **bamf:** bound optimizer step validation ([c4f51fe](https://github.com/Entif-AI/Bilqis-MLX/commit/c4f51fe767aa795eda7ec95b9c3dc6406164a632))
* **bamf:** cache accepted parent fixed-school assessment ([55a53d1](https://github.com/Entif-AI/Bilqis-MLX/commit/55a53d1e70a98164ca08e0744125f7c0ad83a960))
* **bamf:** candidate throughput - remove host trial clone round-trip ([#1284](https://github.com/Entif-AI/Bilqis-MLX/issues/1284)) ([2e98e29](https://github.com/Entif-AI/Bilqis-MLX/commit/2e98e29bfbc64435a49d5d91a894b510a3f3b83b))
* **bamf:** carry bound feature rows through frame encoder [#1264](https://github.com/Entif-AI/Bilqis-MLX/issues/1264) ([f01f9aa](https://github.com/Entif-AI/Bilqis-MLX/commit/f01f9aad6416dec578fcd62a5b389121c796da92))
* **bamf:** carry bound source authority on B11 rows [#1264](https://github.com/Entif-AI/Bilqis-MLX/issues/1264) ([88f146a](https://github.com/Entif-AI/Bilqis-MLX/commit/88f146ab687885acc6822fcb9f63d5f831b408ce))
* **bamf:** carry sealed authorities through frame encoder [#1264](https://github.com/Entif-AI/Bilqis-MLX/issues/1264) ([70dd5b8](https://github.com/Entif-AI/Bilqis-MLX/commit/70dd5b8746ab530cbed3f16891f19bb70f6bc2a5))
* **bamf:** compact frontier planning history ([87c92ea](https://github.com/Entif-AI/Bilqis-MLX/commit/87c92eae30050bfe9743e98313fa31b834d764e7))
* **bamf:** complete candidate identity reuse [#1238](https://github.com/Entif-AI/Bilqis-MLX/issues/1238) ([ca606e4](https://github.com/Entif-AI/Bilqis-MLX/commit/ca606e4dab0ed1cde7d3822e067f870c5d724e9e))
* **bamf:** consume prequalified motif feature rows [#1264](https://github.com/Entif-AI/Bilqis-MLX/issues/1264) ([d0fabf8](https://github.com/Entif-AI/Bilqis-MLX/commit/d0fabf86efa83dded37b1a4073f701f12e6e5771))
* **bamf:** consume prequalified source handoff in embedding [#1264](https://github.com/Entif-AI/Bilqis-MLX/issues/1264) ([e306773](https://github.com/Entif-AI/Bilqis-MLX/commit/e3067735bac51c87d522925abb172afaf8ab1d55))
* **bamf:** expose bound feature rows to compiled encoder [#1264](https://github.com/Entif-AI/Bilqis-MLX/issues/1264) ([0101dda](https://github.com/Entif-AI/Bilqis-MLX/commit/0101ddab06366802b60f979e7357d7dc9a654c01))
* **bamf:** expose sealed authorities to compiled encoder [#1264](https://github.com/Entif-AI/Bilqis-MLX/issues/1264) ([a0271f9](https://github.com/Entif-AI/Bilqis-MLX/commit/a0271f9c9ca14f96462704ed6a94f4d2d57ec93c))
* **bamf:** gate frame factor reuse on issued authority [#1264](https://github.com/Entif-AI/Bilqis-MLX/issues/1264) ([defaa0d](https://github.com/Entif-AI/Bilqis-MLX/commit/defaa0d38f3b6a7d0e23695d88991d4fb6705576))
* **bamf:** gate motif factor reuse on issued authority [#1264](https://github.com/Entif-AI/Bilqis-MLX/issues/1264) ([48cdf41](https://github.com/Entif-AI/Bilqis-MLX/commit/48cdf419ac6e5e5ba30131408e6b7bd68aaaea83))
* **bamf:** index current-generation rejection replay ([f9ddcd1](https://github.com/Entif-AI/Bilqis-MLX/commit/f9ddcd11b416562b36b7ac7fb4a520f741a53eae))
* **bamf:** index rejection replay by journal cursor ([1d3fb37](https://github.com/Entif-AI/Bilqis-MLX/commit/1d3fb37f7f6049980aafda3892929f69ed089b66))
* **bamf:** keep atlas authority hot across visits ([51107e5](https://github.com/Entif-AI/Bilqis-MLX/commit/51107e54dfe9aca5aa4f431c04fbdc5f41ab46c5))
* **bamf:** keep B11 source guard row-scoped [#1264](https://github.com/Entif-AI/Bilqis-MLX/issues/1264) ([900f592](https://github.com/Entif-AI/Bilqis-MLX/commit/900f59288b51bb26af9cc4a869517bdec5be3f9c))
* **bamf:** keep bound feature rows behind issued authority [#1264](https://github.com/Entif-AI/Bilqis-MLX/issues/1264) ([47346eb](https://github.com/Entif-AI/Bilqis-MLX/commit/47346eb7c1aa327256a83220a6ddffa1cf196b83))
* **bamf:** let factor composition consume bound feature rows [#1264](https://github.com/Entif-AI/Bilqis-MLX/issues/1264) ([f7f657e](https://github.com/Entif-AI/Bilqis-MLX/commit/f7f657edab56d282026e94a058b26c9f2ad3ff73))
* **bamf:** make B11 source currentness cheap [#1264](https://github.com/Entif-AI/Bilqis-MLX/issues/1264) ([3e34101](https://github.com/Entif-AI/Bilqis-MLX/commit/3e34101fb519a22a98086a095187db92c20c40c4))
* **bamf:** materialize semantic context once ([36b3e3a](https://github.com/Entif-AI/Bilqis-MLX/commit/36b3e3a68f70aa14ecc2a3ed3ccaee8acec6e695))
* **bamf:** move forensic attestation out of autodiff ([5bd7496](https://github.com/Entif-AI/Bilqis-MLX/commit/5bd74969b9355923dd58ad0e2658258c91b4780f))
* **bamf:** pass bound feature rows through atom embedding [#1264](https://github.com/Entif-AI/Bilqis-MLX/issues/1264) ([af58bd0](https://github.com/Entif-AI/Bilqis-MLX/commit/af58bd03012db429bea32ac6fbc8d625f7ee4c4b))
* **bamf:** pass bound feature rows through frame groups [#1264](https://github.com/Entif-AI/Bilqis-MLX/issues/1264) ([21661e4](https://github.com/Entif-AI/Bilqis-MLX/commit/21661e464b2e1eae9ed8c3c02ea3204fdcaa95a2))
* **bamf:** pass bound source authority into B11 forward [#1264](https://github.com/Entif-AI/Bilqis-MLX/issues/1264) ([582b8de](https://github.com/Entif-AI/Bilqis-MLX/commit/582b8de46c833190c0bc7e0ef5ede336e5d0dfa4))
* **bamf:** pass sealed authority through frame groups [#1264](https://github.com/Entif-AI/Bilqis-MLX/issues/1264) ([5bf73ff](https://github.com/Entif-AI/Bilqis-MLX/commit/5bf73ff1123953b5193abff740806b470cc8f08a))
* **bamf:** pass sealed authority through source encoding [#1264](https://github.com/Entif-AI/Bilqis-MLX/issues/1264) ([e12fdaf](https://github.com/Entif-AI/Bilqis-MLX/commit/e12fdaf5c65d4298eedf9b5e65af328d100511cd))
* **bamf:** pass sealed source authority into motif factors [#1264](https://github.com/Entif-AI/Bilqis-MLX/issues/1264) ([16eda57](https://github.com/Entif-AI/Bilqis-MLX/commit/16eda57f2974d9369b1848b048849e829d00c3d2))
* **bamf:** prefetch native operator source rows ([f92aa64](https://github.com/Entif-AI/Bilqis-MLX/commit/f92aa64535c89fa50861a97a3ff9b9227fef1572))
* **bamf:** prequalify motif feature rows before B11 [#1264](https://github.com/Entif-AI/Bilqis-MLX/issues/1264) ([4de3139](https://github.com/Entif-AI/Bilqis-MLX/commit/4de3139914b5e8b88bece5ccc868fc2dafd5e606))
* **bamf:** preserve B11 source authority through salience [#1264](https://github.com/Entif-AI/Bilqis-MLX/issues/1264) ([461c7b4](https://github.com/Entif-AI/Bilqis-MLX/commit/461c7b4701018f182f137e352f2ee0c632b88a80))
* **bamf:** qualify source authority before B11 [#1264](https://github.com/Entif-AI/Bilqis-MLX/issues/1264) ([efcf69d](https://github.com/Entif-AI/Bilqis-MLX/commit/efcf69d166c0325963a5cc9ee269aa3619c04a53))
* **bamf:** reject partial B11 source authority batches [#1264](https://github.com/Entif-AI/Bilqis-MLX/issues/1264) ([b7abcd5](https://github.com/Entif-AI/Bilqis-MLX/commit/b7abcd574eb81911fd32ec7a2e433a1c66953b54))
* **bamf:** remove duplicate route preflight [#1265](https://github.com/Entif-AI/Bilqis-MLX/issues/1265) ([4a8bd78](https://github.com/Entif-AI/Bilqis-MLX/commit/4a8bd786d21d1ec80ac368cdb8ce7abcaf0dc59a))
* **bamf:** remove duplicate route preflight [#1265](https://github.com/Entif-AI/Bilqis-MLX/issues/1265) ([#1268](https://github.com/Entif-AI/Bilqis-MLX/issues/1268)) ([8d16410](https://github.com/Entif-AI/Bilqis-MLX/commit/8d16410b3a7367861fd21c2d6e1ec32ce06b3cac))
* **bamf:** remove host candidate clone round-trip ([1fdf176](https://github.com/Entif-AI/Bilqis-MLX/commit/1fdf176e9ce7fad8469f69a60ba6ac51e77603ed))
* **bamf:** report B11 source reuse in realized cost [#1264](https://github.com/Entif-AI/Bilqis-MLX/issues/1264) ([2368871](https://github.com/Entif-AI/Bilqis-MLX/commit/236887181ecff1f02fb105f9613f7897f3fed332))
* **bamf:** report structural B11 source reuse honestly [#1264](https://github.com/Entif-AI/Bilqis-MLX/issues/1264) ([28097af](https://github.com/Entif-AI/Bilqis-MLX/commit/28097af29ce16b455fcce028c832a40b2c709a15))
* **bamf:** require exact bound Atlas snapshot in B11 [#1264](https://github.com/Entif-AI/Bilqis-MLX/issues/1264) ([1992b18](https://github.com/Entif-AI/Bilqis-MLX/commit/1992b181ab20a638ff8892193dc2a98d9c1b784c))
* **bamf:** require issued authority for factor reuse [#1264](https://github.com/Entif-AI/Bilqis-MLX/issues/1264) ([809bb0d](https://github.com/Entif-AI/Bilqis-MLX/commit/809bb0dbad2119b5cd522144e665202d245735ac))
* **bamf:** require issued authority in atom embedding [#1264](https://github.com/Entif-AI/Bilqis-MLX/issues/1264) ([42e7805](https://github.com/Entif-AI/Bilqis-MLX/commit/42e7805ed6fe269539f957815efb09ae8391709c))
* **bamf:** retain qualified motif schemas in B11 authority [#1264](https://github.com/Entif-AI/Bilqis-MLX/issues/1264) ([bf6b6c7](https://github.com/Entif-AI/Bilqis-MLX/commit/bf6b6c771e76f6437d9dab13005dd78a5c3cc094))
* **bamf:** retain source authority across both motif sites [#1264](https://github.com/Entif-AI/Bilqis-MLX/issues/1264) ([892d88c](https://github.com/Entif-AI/Bilqis-MLX/commit/892d88c1d8806642283f399fcda2b35d5480f7ed))
* **bamf:** retention throughput: restore multi-step candidate horizons ([bc5f857](https://github.com/Entif-AI/Bilqis-MLX/commit/bc5f8572ade2ebeb6fa10313b846873dc786cf72))
* **bamf:** reuse authenticated atlas context ([00c187b](https://github.com/Entif-AI/Bilqis-MLX/commit/00c187bba37a3bbcced5e19a961a567fe361d719))
* **bamf:** reuse authenticated Atlas context across training [#1234](https://github.com/Entif-AI/Bilqis-MLX/issues/1234) ([cde85fe](https://github.com/Entif-AI/Bilqis-MLX/commit/cde85fe91e251b65f844befffcd3e2f3f0f47ea3))
* **bamf:** reuse authenticated publication state ([1b7f9fa](https://github.com/Entif-AI/Bilqis-MLX/commit/1b7f9faa4dc69a326551192f65c74081b809f708))
* **bamf:** reuse authenticated snapshot for motif schemas [#1264](https://github.com/Entif-AI/Bilqis-MLX/issues/1264) ([29627e3](https://github.com/Entif-AI/Bilqis-MLX/commit/29627e369d8d3f11aebd6f9c49bdf52df72932ef))
* **bamf:** reuse bound feature rows in frame encoding [#1264](https://github.com/Entif-AI/Bilqis-MLX/issues/1264) ([f2e6c2a](https://github.com/Entif-AI/Bilqis-MLX/commit/f2e6c2a654c1f6df1ebb5a5f56a2e693efba18bb))
* **bamf:** reuse bound feature rows in frame factors [#1264](https://github.com/Entif-AI/Bilqis-MLX/issues/1264) ([3ed3488](https://github.com/Entif-AI/Bilqis-MLX/commit/3ed3488f298015ecb503c1741ba67c8b3bcba6e9))
* **bamf:** reuse bound feature rows in source h0 [#1264](https://github.com/Entif-AI/Bilqis-MLX/issues/1264) ([111630f](https://github.com/Entif-AI/Bilqis-MLX/commit/111630fd9b0417a04274cc04527b2267e7b8a304))
* **bamf:** reuse hydrated accepted generation ([7b22d81](https://github.com/Entif-AI/Bilqis-MLX/commit/7b22d81bfab174a0e113fa007273030094beb307))
* **bamf:** reuse immutable candidate identity [#1238](https://github.com/Entif-AI/Bilqis-MLX/issues/1238) ([c91eebb](https://github.com/Entif-AI/Bilqis-MLX/commit/c91eebb5c577c0e38bcaa564bb45efae912a472e))
* **bamf:** reuse motif factor authority inside B08 [#1264](https://github.com/Entif-AI/Bilqis-MLX/issues/1264) ([13ee46e](https://github.com/Entif-AI/Bilqis-MLX/commit/13ee46ef553da4f68bec1b42236f0cd7285eb8e8))
* **bamf:** reuse one hydrated accepted generation per operator visit ([2fc77a9](https://github.com/Entif-AI/Bilqis-MLX/commit/2fc77a99b14aeb71a3c071ce1c3497cca37f418e))
* **bamf:** reuse pinned motif snapshot [#1264](https://github.com/Entif-AI/Bilqis-MLX/issues/1264) ([0d73443](https://github.com/Entif-AI/Bilqis-MLX/commit/0d73443c287a5d69a78b77715ff4ec589e729dd9))
* **bamf:** reuse prepared source qualification ([d1de44e](https://github.com/Entif-AI/Bilqis-MLX/commit/d1de44e1829f4775d4295315f3ed8d2bceea68a0))
* **bamf:** reuse prepared source qualification ([#1273](https://github.com/Entif-AI/Bilqis-MLX/issues/1273)) ([#1296](https://github.com/Entif-AI/Bilqis-MLX/issues/1296)) ([b6e2236](https://github.com/Entif-AI/Bilqis-MLX/commit/b6e22365db4125184ac6e02c19557504e6b28576))
* **bamf:** reuse qualified B11 source authority ([#1264](https://github.com/Entif-AI/Bilqis-MLX/issues/1264)) ([#1267](https://github.com/Entif-AI/Bilqis-MLX/issues/1267)) ([4fbe250](https://github.com/Entif-AI/Bilqis-MLX/commit/4fbe25028e001eaef5fae89af26f39493325e066))
* **bamf:** reuse qualified motif context in B08 reads [#1264](https://github.com/Entif-AI/Bilqis-MLX/issues/1264) ([ab1226c](https://github.com/Entif-AI/Bilqis-MLX/commit/ab1226c95b3890af735b7f7d4e48603a03636886))
* **bamf:** reuse qualified motif schemas in B08 [#1264](https://github.com/Entif-AI/Bilqis-MLX/issues/1264) ([b96bf31](https://github.com/Entif-AI/Bilqis-MLX/commit/b96bf3106eb87c35a64917e7867fd96425571f77))
* **bamf:** stop replaying full frontier history [#1240](https://github.com/Entif-AI/Bilqis-MLX/issues/1240) ([#1262](https://github.com/Entif-AI/Bilqis-MLX/issues/1262)) ([d45e986](https://github.com/Entif-AI/Bilqis-MLX/commit/d45e986ea4d948b5b0b8eccfa7828da3a35c960f))
* **bamf:** thread bound source authority through encoding [#1264](https://github.com/Entif-AI/Bilqis-MLX/issues/1264) ([696e981](https://github.com/Entif-AI/Bilqis-MLX/commit/696e98182414799e2c75980db59dd2da618b44bf))
* **bamf:** thread source authority through B11 producer [#1264](https://github.com/Entif-AI/Bilqis-MLX/issues/1264) ([09e3d83](https://github.com/Entif-AI/Bilqis-MLX/commit/09e3d83bf1399bc5e09c18cd151da9af4fa9de65))
* **bamf:** throughput - bind execution generation once per state ([406e30c](https://github.com/Entif-AI/Bilqis-MLX/commit/406e30c65c257230b50259d678ed4e1e2a880f14))
* **bamf:** trainer exposes live per-step performance observability ([#1269](https://github.com/Entif-AI/Bilqis-MLX/issues/1269)) ([a67682d](https://github.com/Entif-AI/Bilqis-MLX/commit/a67682d63167e0e40cf52678ee90981abf9b2b46))
* **bamf:** trust B11 source authority within gradient launch ([#1272](https://github.com/Entif-AI/Bilqis-MLX/issues/1272)) ([e4cfb77](https://github.com/Entif-AI/Bilqis-MLX/commit/e4cfb77a552f4cfec985c36e20d8a257267f3eb5))
* **bamf:** trust B11 source authority within gradient launch ([#1274](https://github.com/Entif-AI/Bilqis-MLX/issues/1274)) ([82cb41b](https://github.com/Entif-AI/Bilqis-MLX/commit/82cb41b551759aee670a572ece053eb49b060fe0))
* **bamf:** trust source batch authority during compile [#1273](https://github.com/Entif-AI/Bilqis-MLX/issues/1273) ([2de3f88](https://github.com/Entif-AI/Bilqis-MLX/commit/2de3f884d4cf2b603332e064e3f37a8dcb0da136))
* **bamf:** vectorize C08 microbatches ([53d5b87](https://github.com/Entif-AI/Bilqis-MLX/commit/53d5b87f9bc7ca5f5ab448c78984fd885dfad83e))
* **bamf:** vectorize C08 MLX microbatches ([0b0ed5f](https://github.com/Entif-AI/Bilqis-MLX/commit/0b0ed5f069d0ee2adc3928f079e6ab2d0f3e3a57))
* **bamf:** vectorize C08 route microbatches ([950bbbb](https://github.com/Entif-AI/Bilqis-MLX/commit/950bbbbe8e7fe4b471d60fea368c34332ff04909))
* **bamf:** vectorize C08 route microbatches [#1236](https://github.com/Entif-AI/Bilqis-MLX/issues/1236) ([7b753b2](https://github.com/Entif-AI/Bilqis-MLX/commit/7b753b29bb9a7d28b8e16d80febc9aa0a3698f60))
* **bamf:** wire native operator source prefetch ([3b14940](https://github.com/Entif-AI/Bilqis-MLX/commit/3b149403c61f3a291fe34eab635a4fa38768bdcb))
* **planner:** bind accepted custody once per visit ([c52a5b0](https://github.com/Entif-AI/Bilqis-MLX/commit/c52a5b062b9b2f52bc8cfc84abb78c62f458f3b9))
* **planner:** retain accepted correction authority ([2c1b87a](https://github.com/Entif-AI/Bilqis-MLX/commit/2c1b87a4a0573a0621a2b977b024abdcfbab8f55))
* **planner:** reuse planning authority in requalification ([aa2d86a](https://github.com/Entif-AI/Bilqis-MLX/commit/aa2d86a5e38d8bf31543b4763d9978a39c897833))
* **planner:** reuse trusted candidate frontier ([4635d0a](https://github.com/Entif-AI/Bilqis-MLX/commit/4635d0a4f218f3168bf346cbfe9132cca58d0f13))
* **planner:** reuse trusted frontier and planning authority ([edf6934](https://github.com/Entif-AI/Bilqis-MLX/commit/edf6934ff0906dac9640bca7273f924e2b0390a1))
* **retention:** batch fixed-school MLX evaluation ([8390a7a](https://github.com/Entif-AI/Bilqis-MLX/commit/8390a7aedffc7e0e353b73d9a7868f6307a445bd))
* **retention:** batch fixed-school MLX evaluation ([0c5ef1c](https://github.com/Entif-AI/Bilqis-MLX/commit/0c5ef1cda57aea63747609483696a8374b0539b6))
* **retention:** stream versioned candidate content identities ([1b8dd16](https://github.com/Entif-AI/Bilqis-MLX/commit/1b8dd162de9db83b921a282f3b1c5154196552f9))
* **retention:** stream versioned candidate state identity ([16011ce](https://github.com/Entif-AI/Bilqis-MLX/commit/16011cef2c32f0fbf4bab3ea80be8209f721f0cb))
* **runtime:** cache accepted parent assessment ([4e5d325](https://github.com/Entif-AI/Bilqis-MLX/commit/4e5d3250dca0f44006b14ff5e66be1c49469e0c4))

## [1.1.0](https://github.com/Entif-AI/Bilqis-MLX/compare/v1.0.0...v1.1.0) (2026-11-13)

### BAMF-0.2 unified-history cutover

This release joins the complete reviewed BAMF-0.2 unified lineage to `main`. The mainline bridge in [#1029](https://github.com/Entif-AI/Bilqis-MLX/pull/1029) imported the reviewed parallel history after `v1.0.0`; the complete release DAG through `21a84db` contains **2,996 commits**, including **2,264 commit subjects that explicitly name BAMF**. Because that history arrived through a merge parent, the normal Release Please traversal surfaced only the small linear tip and under-reported the release. This section is the explicit `v1.1.0` history backfill.

The release DAG contains **374 feat**, **767 fix**, **9 perf**, **216 refactor**, **645 docs**, **298 test**, **1 build**, **23 ci**, **199 chore**, and **464 merge/non-conventional** commits. The complete 2,996-commit inventory is embedded below in this changelog; see also the [GitHub DAG comparison](https://github.com/Entif-AI/Bilqis-MLX/compare/v1.0.0...21a84dba60b19027ae77fdfe4b722ff860a2f3f8).


### Features

* **bamf:** close delivery with immutable conformance receipts (BAMF-0.2 C15) ([057638a](https://github.com/Entif-AI/Bilqis-MLX/commit/057638a2c93cd152516457c6a5b0b92a946454c1))
* **bamf:** consume accepted C14 for C15 closeout ([e845036](https://github.com/Entif-AI/Bilqis-MLX/commit/e84503682d494f19dece9f531aa4e94e40a4e9a3))
* **bamf:** consume C15 requalification receipts ([c3649b5](https://github.com/Entif-AI/Bilqis-MLX/commit/c3649b50105325847730e15148966f8369c73342))
* **bamf:** declare developmental program (BAMF-0.2 C14.1a) ([8a8c974](https://github.com/Entif-AI/Bilqis-MLX/commit/8a8c9744c5c10f8290f1e717b0adc1cbc5ccf191))
* **bamf:** deliver source-coverage training runbook (BAMF-0.2 C14.2) ([7550492](https://github.com/Entif-AI/Bilqis-MLX/commit/7550492c63eba163daf7d5a0397ab7896cee349b))
* **bamf:** enforce C13 source binding reservation (BAMF-0.2 [#1030](https://github.com/Entif-AI/Bilqis-MLX/issues/1030)b) ([42c17e5](https://github.com/Entif-AI/Bilqis-MLX/commit/42c17e54bc2e9e2bcea2d82cfe545221498ba62d))
* **bamf:** move C09 authority to fixed ordinary-user store (BAMF-0.2 [#1031](https://github.com/Entif-AI/Bilqis-MLX/issues/1031)) ([05a32ba](https://github.com/Entif-AI/Bilqis-MLX/commit/05a32baa0c3ced5e986c7de74b1403c1225dc43d))
* **bamf:** publish C15 ready-for-owner-merge state ([e8262d0](https://github.com/Entif-AI/Bilqis-MLX/commit/e8262d01093fa5ee77991a482d60c8b99585d9e2))
* **bamf:** publish integrated wiring receipt and dashboard handoff (BAMF-0.2 C13.3) ([9e06ea5](https://github.com/Entif-AI/Bilqis-MLX/commit/9e06ea557c910bae7ecd879fe83f4d50aed84eb9))
* **bamf:** reconcile rollback, resume and correction proofs (BAMF-0.2 C13.2) ([b99810c](https://github.com/Entif-AI/Bilqis-MLX/commit/b99810cbf69bf6a379e00056fdec9845dca1245d))
* **bamf:** recursive grade-neutral domain succession (BAMF-0.2 C14.3) ([de84266](https://github.com/Entif-AI/Bilqis-MLX/commit/de84266ba3db79b6545ff484f3268a99ea8872f6))
* **bamf:** select lawful interleaved stages (BAMF-0.2 C14.1b) ([6719eb5](https://github.com/Entif-AI/Bilqis-MLX/commit/6719eb506bd2b8f2fc2ba92b9113f9b734395295))
* **bamf:** turn in integrated M3 Ultra wiring path (BAMF-0.2 C13.1) ([47e57f0](https://github.com/Entif-AI/Bilqis-MLX/commit/47e57f05574b7702a85772003c5fc892ff206a33))


### Bug Fixes

* **bamf:** bind C15 proof to executable owner tests ([c4197f2](https://github.com/Entif-AI/Bilqis-MLX/commit/c4197f28c4aa2e3972634b1dbea255832d4b6d7b))
* **bamf:** bound live issue newline transport ([8fd258a](https://github.com/Entif-AI/Bilqis-MLX/commit/8fd258a625f4d7d8c10fd08521594fc0f27960f5))
* **bamf:** move C09 authority to ordinary-user store ([#1031](https://github.com/Entif-AI/Bilqis-MLX/issues/1031)) ([bc283e9](https://github.com/Entif-AI/Bilqis-MLX/commit/bc283e9480b4dd60957ef5eaafe86dc7bff08496))
* **bamf:** reconcile C13 release boundary for C15 ([a72192b](https://github.com/Entif-AI/Bilqis-MLX/commit/a72192b0b0cb0fa5aade1f87dd2677603cbcee51))
* **bamf:** reserve C13 source binding namespace ([#1032](https://github.com/Entif-AI/Bilqis-MLX/issues/1032)) ([07cdf41](https://github.com/Entif-AI/Bilqis-MLX/commit/07cdf41380a6f325f72de9d3b64e7451f74fcca7))


### Complete release history

The following is the complete `v1.0.0..v1.1.0` commit inventory for this release, including the BAMF unified history imported through the bridge merge. Oldest first.

Oldest first. This inventory is provenance for the release cutover; the human-facing changelog remains grouped and concise.

- [`05f34cfa7fb9`](https://github.com/Entif-AI/Bilqis-MLX/commit/05f34cfa7fb977a09dfd575ac2d1cfe64637dcdd) `docs(factory): codify #150 microspec boundary`
- [`fd3abb92beb2`](https://github.com/Entif-AI/Bilqis-MLX/commit/fd3abb92beb23d1bf9fac9835e718521b064c30a) `docs(factory): freeze #150 leaf workstack`
- [`eef88897b703`](https://github.com/Entif-AI/Bilqis-MLX/commit/eef88897b703e1d7bb0eef01155093a8e3258928) `docs(factory): bind #150 execution issues`
- [`4e794e681979`](https://github.com/Entif-AI/Bilqis-MLX/commit/4e794e68197934407f05bdac5000d3e711260f92) `fix(factory): guard current APIs against legacy Course authority`
- [`778e9a8cf26d`](https://github.com/Entif-AI/Bilqis-MLX/commit/778e9a8cf26d49c30e2fffa38e532dd0b20aad7d) `fix(factory): require an executable release gate for training`
- [`d292d11a478b`](https://github.com/Entif-AI/Bilqis-MLX/commit/d292d11a478ba7b3de9491c2fa8db42f1e2c27ca) `fix(factory): enforce trainer dependency direction by module identity`
- [`5a46a1c045fd`](https://github.com/Entif-AI/Bilqis-MLX/commit/5a46a1c045fd1dfb60d00f9f68e46132e63b4d3f) `feat(factory): quarantine compatibility writer calls`
- [`466d0d6cc373`](https://github.com/Entif-AI/Bilqis-MLX/commit/466d0d6cc37365fca73f41403e0ebfea690891be) `feat(factory): separate v2 twelve-capability grade capacity`
- [`bfafe9929757`](https://github.com/Entif-AI/Bilqis-MLX/commit/bfafe99297579cc61f94a0ccc9e6209dfb883049) `feat(factory): guard semantic identity dispatch boundaries`
- [`e170cb983f14`](https://github.com/Entif-AI/Bilqis-MLX/commit/e170cb983f144ceb09ef98981689b5ebd6a8c3dd) `test(factory): prove twelve-capability v2 execution plans`
- [`f769844c6280`](https://github.com/Entif-AI/Bilqis-MLX/commit/f769844c6280e74567264616b2f7c439e8e0637e) `test(factory): verify twelve-capability v2 release roundtrip`
- [`02a918b551dd`](https://github.com/Entif-AI/Bilqis-MLX/commit/02a918b551ddb43ae45e3e4be5b2d2866d213b14) `test(factory): preserve all twelve staged plan bindings`
- [`e1d229df70a5`](https://github.com/Entif-AI/Bilqis-MLX/commit/e1d229df70a5bd5ae557daeab8274e712b232a07) `test(factory): bind twelve-capability evidence and assessment seals`
- [`44b448ed5729`](https://github.com/Entif-AI/Bilqis-MLX/commit/44b448ed57298a972ddb413f83ddbacb0deff24d) `test(factory): exercise twelve capabilities through provider bindings`
- [`934b9ed6eafd`](https://github.com/Entif-AI/Bilqis-MLX/commit/934b9ed6eafdc5255aa0852743b23cd0bf6123e9) `test(factory): preserve twelve-capability schedule scope`
- [`d2611af038ba`](https://github.com/Entif-AI/Bilqis-MLX/commit/d2611af038bae696d87b2da5bec88c88a4c5684d) `test(factory): project thin profiles from twelve-capability horizons`
- [`89a67da73c1c`](https://github.com/Entif-AI/Bilqis-MLX/commit/89a67da73c1c170c602c1e4d397db73ff76c9791) `test(factory): preserve twelve-capability successor lineage`
- [`88f196d9b2ec`](https://github.com/Entif-AI/Bilqis-MLX/commit/88f196d9b2ecb5f031fe1cbc77330949d313da0a) `feat(runtime): bind source execution to verified factory releases`
- [`cf8797d33973`](https://github.com/Entif-AI/Bilqis-MLX/commit/cf8797d33973945de6ed01e655e76361b0c65c6b) `feat(runtime): construct source contexts from admitted release readback`
- [`b93a52c468f3`](https://github.com/Entif-AI/Bilqis-MLX/commit/b93a52c468f392adc22132ac158e0f137dd81749) `refactor(factory)!: remove generation legacy course keyword`
- [`33e59c3f9e3e`](https://github.com/Entif-AI/Bilqis-MLX/commit/33e59c3f9e3e33dac73ea770347b95e4f9e678ef) `refactor(factory)!: remove compiler legacy course inputs`
- [`01e352f2d801`](https://github.com/Entif-AI/Bilqis-MLX/commit/01e352f2d8011bda2da9d1ab7a187671e1a2faec) `feat(assessment): draw through bound v2 source context`
- [`28cad506c85e`](https://github.com/Entif-AI/Bilqis-MLX/commit/28cad506c85ead5609cf98e84c6dcee0c8a3a7e0) `feat(factory): bind releases to the full semantic graph`
- [`3da1e9ed635e`](https://github.com/Entif-AI/Bilqis-MLX/commit/3da1e9ed635e806f09eb8f4ae49cb2f453b8b6cb) `feat(factory): derive instructional constituent root closure`
- [`a3f347686e39`](https://github.com/Entif-AI/Bilqis-MLX/commit/a3f347686e393ef5c94c50ea0bb9d24cf56029df) `refactor(runtime): compile adopted profiles from v2 authority`
- [`38ba6bf29823`](https://github.com/Entif-AI/Bilqis-MLX/commit/38ba6bf298236afc485bd15c99a7900663058dca) `fix(runtime): keep admitted resume on v2 schedule authority`
- [`ad37d406dae1`](https://github.com/Entif-AI/Bilqis-MLX/commit/ad37d406dae14525c27b09b2411d8ccc2be9cb24) `refactor(runtime): keep operating loop on admitted schedules`
- [`b0944670a421`](https://github.com/Entif-AI/Bilqis-MLX/commit/b0944670a421a8c6dc4837f3e248118236283075) `fix(factory): prefer admitted release scheduling authority`
- [`15747ea0ea0c`](https://github.com/Entif-AI/Bilqis-MLX/commit/15747ea0ea0c17467d52508d2ff9e6dc33ed87ee) `feat(scheduler): classify schedule topology independently of ABI`
- [`6dfecb3e3811`](https://github.com/Entif-AI/Bilqis-MLX/commit/6dfecb3e3811967a529a2af4147d183c6970684b) `test(scheduler): prove arbitrary appended grade custody`
- [`6598fd56420e`](https://github.com/Entif-AI/Bilqis-MLX/commit/6598fd56420e4a942852009df945625550bed1d7) `test(scheduler): prove opaque capability identity scheduling`
- [`05be9f99f35e`](https://github.com/Entif-AI/Bilqis-MLX/commit/05be9f99f35e7e2d3703102dbcf80e932c401834) `refactor(runtime): own historical revision transaction`
- [`483ab6134934`](https://github.com/Entif-AI/Bilqis-MLX/commit/483ab6134934963b28abfb24253112e04b4be8aa) `refactor(runtime): own historical replacement transaction`
- [`7fea17c88868`](https://github.com/Entif-AI/Bilqis-MLX/commit/7fea17c88868da5b42761cb6920974de44e3c8b7) `fix(factory): route prefetch through release context`
- [`208a5a036a24`](https://github.com/Entif-AI/Bilqis-MLX/commit/208a5a036a24028432f92066c52a7c20de76dc1c) `test(curriculum): isolate thin-debt integration fixture`
- [`34b5f93a38df`](https://github.com/Entif-AI/Bilqis-MLX/commit/34b5f93a38dfcd6bebb05b720051aa08ef84cd8f) `feat(curriculum): parameterize debt cadence policy`
- [`dcdb30f86873`](https://github.com/Entif-AI/Bilqis-MLX/commit/dcdb30f86873ae24655aa74b52868599a3eb849d) `feat(runtime): own legacy grade append transaction`
- [`47756019fdee`](https://github.com/Entif-AI/Bilqis-MLX/commit/47756019fdeee08d16bb854e8bba835ac4bdd1ba) `refactor(runtime): own known grade boundary dispatch`
- [`01b427d649f1`](https://github.com/Entif-AI/Bilqis-MLX/commit/01b427d649f190697752496b040419851c8fc707) `docs(factory): use page-local issue navigation`
- [`2b8af82dcfe8`](https://github.com/Entif-AI/Bilqis-MLX/commit/2b8af82dcfe8774056945cc7120c705b9142e63b) `docs(handoff): checkpoint issue 150 reconciliation`
- [`fbd814a1959c`](https://github.com/Entif-AI/Bilqis-MLX/commit/fbd814a1959c2b85b563282eda1acc15b18dcf1e) `docs(handoff): record context transfer boundary`
- [`83c888d908e6`](https://github.com/Entif-AI/Bilqis-MLX/commit/83c888d908e6cc2e9670c603ce9031be34218bfe) `refactor(runtime): retire compatibility transition writer`
- [`657b3cf088a9`](https://github.com/Entif-AI/Bilqis-MLX/commit/657b3cf088a94cc72727d8ee1c7941aed578a4a3) `test(compatibility): freeze translation boundary and facade signatures`
- [`2281ffe3a743`](https://github.com/Entif-AI/Bilqis-MLX/commit/2281ffe3a74367b685c0637e9670a181b407b65b) `test(runtime): prove implementation drift blocks JIT admission`
- [`a35fd5ce1ba1`](https://github.com/Entif-AI/Bilqis-MLX/commit/a35fd5ce1ba1be2ad8ff6e996d8831ac986a5767) `fix(runtime): filter staged packages against answer implementations`
- [`77a31d738c92`](https://github.com/Entif-AI/Bilqis-MLX/commit/77a31d738c920288932ed06f120882529564cbce) `test(runtime): prove admitted source footprint stays closed`
- [`60653cfd80db`](https://github.com/Entif-AI/Bilqis-MLX/commit/60653cfd80db52faa418bf287e1fa8c060bb8740) `fix(runtime): verify frontier custody before catalog growth`
- [`653eaea96c18`](https://github.com/Entif-AI/Bilqis-MLX/commit/653eaea96c18743145b1f3a6cf5bdced47db86f8) `fix(runtime): validate prefetch footprint before source draws`
- [`7932c579be8e`](https://github.com/Entif-AI/Bilqis-MLX/commit/7932c579be8e490eda77796ffacc0419bb5a8ed8) `fix(compatibility): restore read-only historical preflight`
- [`c6949f061cb9`](https://github.com/Entif-AI/Bilqis-MLX/commit/c6949f061cb9558a4933c1e08d21987d0f25f699) `test(factory): prove staging preserves ordinary release authority`
- [`6b41ed04fb6f`](https://github.com/Entif-AI/Bilqis-MLX/commit/6b41ed04fb6f165156375e75ca2e0295a26e6d53) `fix(factory): verify realized graph against staged release`
- [`f1ca7e441e80`](https://github.com/Entif-AI/Bilqis-MLX/commit/f1ca7e441e80334e86682899e5a06f53608d9269) `test(runtime): bind prepared proposals to live context`
- [`d427c5dfae58`](https://github.com/Entif-AI/Bilqis-MLX/commit/d427c5dfae583a23e0cadc9dfd70099d73b8bb51) `test(runtime): assert exact predecessor drift code`
- [`c9357b792123`](https://github.com/Entif-AI/Bilqis-MLX/commit/c9357b792123dac5f4c8bea15a89f2bb5e92ee72) `refactor(runtime): unify prepared successor adoption entry`
- [`9e27d1271bc5`](https://github.com/Entif-AI/Bilqis-MLX/commit/9e27d1271bc5e898e0cb3142de4bd023ac1df319) `fix(runtime): separate schedule topology from ABI growth`
- [`5ccc673ddca9`](https://github.com/Entif-AI/Bilqis-MLX/commit/5ccc673ddca9c4ce1f46875b5ab4ed12694fe62f) `refactor(runtime): make same-ABI materialization explicit`
- [`796ef0a6de01`](https://github.com/Entif-AI/Bilqis-MLX/commit/796ef0a6de01975504af59dc9a9e47f093cbb6c7) `refactor(runtime): share append-only successor materialization`
- [`185925973121`](https://github.com/Entif-AI/Bilqis-MLX/commit/18592597312172c5c44f335df8ad9dc1257e3395) `refactor(runtime): unify prepared successor admission tail`
- [`26bc12fa790f`](https://github.com/Entif-AI/Bilqis-MLX/commit/26bc12fa790f2fea9d58116283be944fc4bd3bbc) `feat(factory): register runtime semantic footprint callbacks`
- [`cbe292346012`](https://github.com/Entif-AI/Bilqis-MLX/commit/cbe29234601277034a981ad64612704f44b08d4e) `refactor(sources): own school verification and semantic footprints`
- [`0a36be841cb7`](https://github.com/Entif-AI/Bilqis-MLX/commit/0a36be841cb73caa382e76cf17a7346b7c745e05) `refactor(sources): resolve declared Boolean evidence producers`
- [`37a1262ab15c`](https://github.com/Entif-AI/Bilqis-MLX/commit/37a1262ab15c0ff13afdef2325a70eca0d8f87ee) `refactor(retention): own immutable fragile preservation policy`
- [`4d5c78980714`](https://github.com/Entif-AI/Bilqis-MLX/commit/4d5c789807141f6d74262fc239b073af32203173) `refactor(retention): delegate fragile semantics to source callbacks`
- [`8110752a65ea`](https://github.com/Entif-AI/Bilqis-MLX/commit/8110752a65eac9adb28c26aeadd5a8de713d655d) `refactor(retention): share fresh preservation selection`
- [`c22a026e9b62`](https://github.com/Entif-AI/Bilqis-MLX/commit/c22a026e9b628a5eca444b912a262708b4eb3ce5) `refactor(retention): consume frozen candidate policy`
- [`f668ba0f05d5`](https://github.com/Entif-AI/Bilqis-MLX/commit/f668ba0f05d5d34b91ee0bfe235663c1a5105e7a) `refactor(prefetch): resolve generic preservation policy`
- [`4ebcad235297`](https://github.com/Entif-AI/Bilqis-MLX/commit/4ebcad235297a17a88fad4a5c3fd0df78aaa6320) `refactor(telemetry): isolate historical event fallbacks`
- [`b77357f1e116`](https://github.com/Entif-AI/Bilqis-MLX/commit/b77357f1e1160b9928b1718d8ca964a979f832a7) `refactor(cli): isolate historical preflight descriptors`
- [`74069ebef359`](https://github.com/Entif-AI/Bilqis-MLX/commit/74069ebef359ea03422e8ff97ee052a8031fb953) `test(runtime): prove delayed same-ABI prepared adoption`
- [`b6fd6f73b2e3`](https://github.com/Entif-AI/Bilqis-MLX/commit/b6fd6f73b2e30e185e6a17a0b2761254771b8527) `test(runtime): prove same-grade native vocabulary growth`
- [`64b2b4fbd478`](https://github.com/Entif-AI/Bilqis-MLX/commit/64b2b4fbd478c7760dc91e3caec2884e3058528b) `docs: record Conjoined Triangle authority decisions`
- [`ec9a97046f12`](https://github.com/Entif-AI/Bilqis-MLX/commit/ec9a97046f1285d3274af42b9dedfc589c800a75) `test(runtime): prove prepared recovery byte idempotence`
- [`d3a7c933d083`](https://github.com/Entif-AI/Bilqis-MLX/commit/d3a7c933d083cce28b58e6b478eccd84d53e18ca) `fix(source): separate numeric semantics and provider identity`
- [`aad46c236c7c`](https://github.com/Entif-AI/Bilqis-MLX/commit/aad46c236c7cb7bcb085548638fdf31f679d9128) `refactor(source): retire generic provider verification logic`
- [`76a67fc69b66`](https://github.com/Entif-AI/Bilqis-MLX/commit/76a67fc69b6613a767701ca0833dbae20de11ddf) `fix(factory): enforce instructional closure on v2 specimens`
- [`0305a066b4f3`](https://github.com/Entif-AI/Bilqis-MLX/commit/0305a066b4f39e2b5073c3d3f8735452f0847c24) `fix(teaching): close live v2 enrichment constituents`
- [`5cbd23946df9`](https://github.com/Entif-AI/Bilqis-MLX/commit/5cbd23946df996f70bd9240f11db0704ff3fd8bd) `test(factory): prove twelve-capability direct v2 Grade Z lifecycle`
- [`73aa4e0045d0`](https://github.com/Entif-AI/Bilqis-MLX/commit/73aa4e0045d01ba6e288765a26a849520fe0fe14) `test(factory): prove precompiled fixed-ABI six-grade runway`
- [`9fe358bfc275`](https://github.com/Entif-AI/Bilqis-MLX/commit/9fe358bfc275f9568526e1746a6c2e90ad38a579) `refactor(factory): retire legacy grade transition runtime`
- [`7baca2044ca0`](https://github.com/Entif-AI/Bilqis-MLX/commit/7baca2044ca0a47fa4be4eadefd5ec320f5ea9c0) `refactor(factory): remove legacy course plumbing and named feedback dispatch`
- [`08c17f961100`](https://github.com/Entif-AI/Bilqis-MLX/commit/08c17f9611002c84a3aaf4f837b9abe104358ed9) `refactor(factory): close recovery ownership and runtime architecture`
- [`dac20330d348`](https://github.com/Entif-AI/Bilqis-MLX/commit/dac20330d3486b8b472be511a7717a56dc2debd3) `fix(factory): reject historical resume under v2`
- [`979d95b42da2`](https://github.com/Entif-AI/Bilqis-MLX/commit/979d95b42da20839495bc40203be261bb9a4368d) `fix(ci): clear factory portable hygiene debt`
- [`fd5edd10a9d6`](https://github.com/Entif-AI/Bilqis-MLX/commit/fd5edd10a9d67e182186e1bf45dd8cc86b75daaa) `fix(ci): type extracted owner error contracts`
- [`0a0d73a85d8b`](https://github.com/Entif-AI/Bilqis-MLX/commit/0a0d73a85d8b6214aaa446c04a510d05e904ae5c) `fix(ci): defer neural imports during resume inspection`
- [`a9580db831ee`](https://github.com/Entif-AI/Bilqis-MLX/commit/a9580db831ee904d5b408960e4a4547d09f96a7b) `feat(runtime): make model topology immutable run identity`
- [`f09e44d35b5f`](https://github.com/Entif-AI/Bilqis-MLX/commit/f09e44d35b5f544ef8d3e61ec127e326d0b09eb1) `fix(runtime): derive AdamW arity from its declared contract`
- [`c25610668513`](https://github.com/Entif-AI/Bilqis-MLX/commit/c256106685130108f3c5ee638039302efd7bcd67) `feat(factory): capture replayable teacher observations`
- [`d59b8ddf1fd5`](https://github.com/Entif-AI/Bilqis-MLX/commit/d59b8ddf1fd58e3b72b9b20635a40b6a916809bc) `fix(factory): verify observation replay and preserve unmeasured evidence`
- [`94a9e0301f16`](https://github.com/Entif-AI/Bilqis-MLX/commit/94a9e0301f16790c202058cd7ecd3af609f0c573) `fix(factory): complete teacher observation replay proof`
- [`35cf2b8ccb6c`](https://github.com/Entif-AI/Bilqis-MLX/commit/35cf2b8ccb6c7d0e9f195d7e65e4ef990bfe5994) `docs(factory): refresh observation qualification handoff`
- [`4e54dcf7d394`](https://github.com/Entif-AI/Bilqis-MLX/commit/4e54dcf7d39498b65b5d95f757fbe2474381333a) `feat(factory): freeze controlled learning qualification`
- [`7e7774100ed6`](https://github.com/Entif-AI/Bilqis-MLX/commit/7e7774100ed6403c57bcacc9579d303504527591) `fix(factory): reuse canonical source manifest during freeze`
- [`59fa6bbfd176`](https://github.com/Entif-AI/Bilqis-MLX/commit/59fa6bbfd1765df45277637430acf2a00d9e1e91) `test(factory): isolate portable qualification seams`
- [`6a1656f285ec`](https://github.com/Entif-AI/Bilqis-MLX/commit/6a1656f285ec4ed99a5c4b8dca57204cc43ea57b) `docs(factory): pin the qualification manifest and human review packet`
- [`1edba645615a`](https://github.com/Entif-AI/Bilqis-MLX/commit/1edba645615a150c3ccb928987e4f8b1d76c440b) `fix(factory): use v2 semantic authority in lesson diagnostics`
- [`b4e535c5c05f`](https://github.com/Entif-AI/Bilqis-MLX/commit/b4e535c5c05f057282ff527ae9ac0e57b4f04046) `fix(factory): evaluate qualification against admitted stage`
- [`6c815d4fdaa2`](https://github.com/Entif-AI/Bilqis-MLX/commit/6c815d4fdaa2d6c1978cbad93cd7962d05cb940c) `test(factory): lock staged qualification evaluation`
- [`cbb5d518c232`](https://github.com/Entif-AI/Bilqis-MLX/commit/cbb5d518c23217119d195737b1b411ef22b47bf0) `docs(factory): supersede qualification manifest after launch repairs`
- [`895a15321020`](https://github.com/Entif-AI/Bilqis-MLX/commit/895a15321020c379d4bf4b12a55d55e45511a4a3) `fix(factory): keep lesson authority internal and typed`
- [`e01079a88bf3`](https://github.com/Entif-AI/Bilqis-MLX/commit/e01079a88bf39c723bc0ba191fd4d573960c12d1) `docs(factory): finalize repaired qualification v3`
- [`2e5ee21a97a6`](https://github.com/Entif-AI/Bilqis-MLX/commit/2e5ee21a97a66c683c61f74419da03500c30d2c4) `fix(factory): defer native qualification inference import`
- [`fa71c44edb1b`](https://github.com/Entif-AI/Bilqis-MLX/commit/fa71c44edb1b6d848b6e29e5073704608187951a) `docs(factory): bind qualification v3 to portable fix`
- [`f703f13b44ac`](https://github.com/Entif-AI/Bilqis-MLX/commit/f703f13b44acf205665f6de3842bb5f395087056) `feat(dashboard): replay stable run metrics from 349`
- [`bf4ed4cfe862`](https://github.com/Entif-AI/Bilqis-MLX/commit/bf4ed4cfe86252a7a85ea8b26736aeea462c84cb) `fix(dashboard): preserve all active champions`
- [`5898def7d01d`](https://github.com/Entif-AI/Bilqis-MLX/commit/5898def7d01d0831d5ae86deb711d75896f51a0b) `feat(teacher): replay bounded strategy population from 349`
- [`f5b7b5aa7f72`](https://github.com/Entif-AI/Bilqis-MLX/commit/f5b7b5aa7f727affc60ad1fe592d06dc39153a0b) `feat(teacher): attribute outcomes to realized delivery`
- [`93148522d769`](https://github.com/Entif-AI/Bilqis-MLX/commit/93148522d769b26993d87a3d026da83efa9d84ff) `docs(factory): receipt selective 349 replay policy`
- [`540c72855433`](https://github.com/Entif-AI/Bilqis-MLX/commit/540c72855433b94928054741a8e9a8a75835a25f) `feat(factory): restore proven 349 learning controls`
- [`53494e8b8d31`](https://github.com/Entif-AI/Bilqis-MLX/commit/53494e8b8d31bd7c9d2370788b042a6e58b97698) `feat(dashboard): restore teacher policy health`
- [`d21797e72365`](https://github.com/Entif-AI/Bilqis-MLX/commit/d21797e72365bf93ea7cad3a4ef9020ec9817f23) `feat(dashboard): add policy yield and progression metrics`
- [`8737e99a8015`](https://github.com/Entif-AI/Bilqis-MLX/commit/8737e99a801507ead0ad4ce7f4182fe7416dd74e) `fix(factory): replenish fresh generalization source space`
- [`8724283ac320`](https://github.com/Entif-AI/Bilqis-MLX/commit/8724283ac320c3c1a667de5d245affb6ff07cb5e) `fix(factory): generalize Grade A fresh source context`
- [`5b84eca610f4`](https://github.com/Entif-AI/Bilqis-MLX/commit/5b84eca610f471630ee5c2fb27c15359a58f6766) `fix(dashboard): reconstruct graduation totals from full journal`
- [`13240828cd15`](https://github.com/Entif-AI/Bilqis-MLX/commit/13240828cd15612e9a84f0f6222484cf2e18cb96) `fix(trainer): prevent cumulative mature-grade regression`
- [`3e3cb3674c3e`](https://github.com/Entif-AI/Bilqis-MLX/commit/3e3cb3674c3e0825c8950e1c3edf5ab925635675) `fix(recovery): retain abandoned terminal checkpoint`
- [`79686e19b17b`](https://github.com/Entif-AI/Bilqis-MLX/commit/79686e19b17bc86adbd61890162fa0833d4a9bfb) `fix(trainer): ignore composite draw-pass identity metadata`
- [`554a2007de1a`](https://github.com/Entif-AI/Bilqis-MLX/commit/554a2007de1a920d86d6730dd44527a1bde6b7d0) `fix(teacher): rotate unretained same-student policies`
- [`a0189ed27d0f`](https://github.com/Entif-AI/Bilqis-MLX/commit/a0189ed27d0fff8ec133bf6a02c35e23c57f33ad) `fix(factory): suspend developmental generalization`
- [`0bc8306c3bb0`](https://github.com/Entif-AI/Bilqis-MLX/commit/0bc8306c3bb0c0d5a3df3c1dd8db87e7dd5b70f2) `fix(trainer): align preservation support with retention gates`
- [`4ca32f6b2ae7`](https://github.com/Entif-AI/Bilqis-MLX/commit/4ca32f6b2ae76456e96094232058c73c85588f04) `fix(retention): compare candidates with current parent`
- [`bbaeb27078b5`](https://github.com/Entif-AI/Bilqis-MLX/commit/bbaeb27078b576873f071e5329d734effa1ef079) `revert: excise cumulative mature-grade regression change`
- [`fbd424b1dadb`](https://github.com/Entif-AI/Bilqis-MLX/commit/fbd424b1dadba5e80d43932f53cdedc4e40e3c68) `fix(factory): admit exact 1324082 rollback provider`
- [`2a8c5b14fd65`](https://github.com/Entif-AI/Bilqis-MLX/commit/2a8c5b14fd6558c0b6caab0eb714f75b3c7a7ee2) `fix(retention): bound mature-grade debt and repair it`
- [`4c9a1865eb2b`](https://github.com/Entif-AI/Bilqis-MLX/commit/4c9a1865eb2bcc4d0c8e50aea06322e573b64b4d) `fix(scheduler): bound mature-debt repair passes`
- [`080e3a307740`](https://github.com/Entif-AI/Bilqis-MLX/commit/080e3a30774084cb229b8f73953e395f226eecfc) `fix(scheduler): carry sweep visit into debt repair`
- [`f28c64e8ccfe`](https://github.com/Entif-AI/Bilqis-MLX/commit/f28c64e8ccfe55c3506f787ede8c074182b86dc7) `fix(retention): use grade debt and real exploration`
- [`74b20531da00`](https://github.com/Entif-AI/Bilqis-MLX/commit/74b20531da00177ef3e3a7fd138cb52a19d631ee) `fix(teacher): cool exhausted policies conservatively`
- [`94a3fcfb6c96`](https://github.com/Entif-AI/Bilqis-MLX/commit/94a3fcfb6c967168f8529cd2cd44ab0e6afcb3dd) `fix(scheduler): boost new frontier until median`
- [`86387eb30de7`](https://github.com/Entif-AI/Bilqis-MLX/commit/86387eb30de742b393a42011933bdc62b3e23208) `fix(teacher): breed bespoke scalable strategy population`
- [`8cd11a2aaa42`](https://github.com/Entif-AI/Bilqis-MLX/commit/8cd11a2aaa4295a493b1dd15c3fc6218aaeadb1a) `fix(trainer): restore introot and weakness target identity`
- [`4154e77abb1b`](https://github.com/Entif-AI/Bilqis-MLX/commit/4154e77abb1bb24744c1f3cacdc1c570be70b3b4) `fix(curriculum): restore grade c numeric staircase`
- [`ee9f3356a8eb`](https://github.com/Entif-AI/Bilqis-MLX/commit/ee9f3356a8eb7864b40cbee6e6d816e22b8695c4) `fix(factory): resume adr106 numeric receipts`
- [`6ac7cb65e042`](https://github.com/Entif-AI/Bilqis-MLX/commit/6ac7cb65e04295cd4f8db404faf02164d1614e47) `fix(dashboard): dedupe graduation frontiers`
- [`988e54a0a40d`](https://github.com/Entif-AI/Bilqis-MLX/commit/988e54a0a40dce3b2cae062560f75f7b954591e9) `fix(teacher): retain policy value across numeric scope`
- [`41dce485151e`](https://github.com/Entif-AI/Bilqis-MLX/commit/41dce485151e205cd55be9a71004534905489485) `feat(teacher): evolve beyond legacy policy lattice`
- [`c11b639c662b`](https://github.com/Entif-AI/Bilqis-MLX/commit/c11b639c662bdbe5c07607a13cdf3a88f10637a7) `feat(retention): escape starvation with bounded plasticity`
- [`37678f26faf9`](https://github.com/Entif-AI/Bilqis-MLX/commit/37678f26faf98549749e1aba4124d1676d1c9832) `fix(teacher): reseed exhausted capability population`
- [`5111461cae4b`](https://github.com/Entif-AI/Bilqis-MLX/commit/5111461cae4bf265e08d1a2fea0dae9f59b97a08) `fix(scheduler): keep progression frontier prioritized`
- [`d0dc309c117f`](https://github.com/Entif-AI/Bilqis-MLX/commit/d0dc309c117fa192e77df31ece4715daeb50ea80) `fix(scheduler): restore persisted c priority cadence`
- [`b33ee484c626`](https://github.com/Entif-AI/Bilqis-MLX/commit/b33ee484c626bb1c45ea0f350e33a72ba6f83097) `feat(retention): trigger plasticity on school drought`
- [`5e154f6245aa`](https://github.com/Entif-AI/Bilqis-MLX/commit/5e154f6245aae7ddac2d987d91f99db605f2a614) `fix(scheduler): require blocker progress before promotion retry`
- [`b42aff327d98`](https://github.com/Entif-AI/Bilqis-MLX/commit/b42aff327d985453f6402757117b1c098af81418) `fix(curriculum): restore full B and weight frontier recovery`
- [`6c05c08f2121`](https://github.com/Entif-AI/Bilqis-MLX/commit/6c05c08f2121cb57dd6817e897e899fa057c390d) `fix(stagnation): separate weighted recovery membership`
- [`c1b66360d0b2`](https://github.com/Entif-AI/Bilqis-MLX/commit/c1b66360d0b2765d7c61d7e101beb709f5c4caff) `fix(training): repair methodology authority and plasticity trades`
- [`2aaa8e57b79b`](https://github.com/Entif-AI/Bilqis-MLX/commit/2aaa8e57b79b996e4cd16be8d0c0f7f4405f40cf) `fix(training): exploit retained teacher policies before breeding`
- [`8ef6d46f4d83`](https://github.com/Entif-AI/Bilqis-MLX/commit/8ef6d46f4d83582f3cab3ce61c6e174e844f8c11) `fix(training): focus retention support on gated surfaces`
- [`8414402d2dd8`](https://github.com/Entif-AI/Bilqis-MLX/commit/8414402d2dd8e9d62e3504406613ec6c408aad06) `fix(scheduler): restore bounded B candidate effort`
- [`83199f5565fc`](https://github.com/Entif-AI/Bilqis-MLX/commit/83199f5565fc3bbf15bdd724f8a421a841559229) `fix(teacher): align shadow deltas with correct-answer units`
- [`d84d2ab9e2d7`](https://github.com/Entif-AI/Bilqis-MLX/commit/d84d2ab9e2d79817c131ef7e0d4ec0d574e57b32) `refactor(scheduler): generalize bounded debt cadence roles`
- [`77d4f6869b78`](https://github.com/Entif-AI/Bilqis-MLX/commit/77d4f6869b782fc24341e6e6ec8f2601e1dd3873) `chore(bamf): create unified factory skos planning base`
- [`3cb1964f38fa`](https://github.com/Entif-AI/Bilqis-MLX/commit/3cb1964f38fa85cec203b1b4a2076c2424cdd7bc) `docs(adr): version future work specs with implementation`
- [`44f78431709e`](https://github.com/Entif-AI/Bilqis-MLX/commit/44f78431709ec3b8fc23f47b45d9b18f167c7354) `docs(bamf): bind issues to reviewed lane branches`
- [`4a700e429632`](https://github.com/Entif-AI/Bilqis-MLX/commit/4a700e42963271e41403a5ad0287113fbf00f79e) `docs(bamf): authorize sequential Lane A batch execution`
- [`740caa41bde3`](https://github.com/Entif-AI/Bilqis-MLX/commit/740caa41bde3c1f93d6810833864cc3ca0c61044) `feat(semantics): bind canonical atlas identities`
- [`20c97c19a092`](https://github.com/Entif-AI/Bilqis-MLX/commit/20c97c19a092b05703f1beaf7c645228d703fed5) `docs(bamf): normalize A01.1 evidence`
- [`c764d5b68f02`](https://github.com/Entif-AI/Bilqis-MLX/commit/c764d5b68f0254c3bba68524bc38c75664c0a484) `feat(runtime): stage BAMF v2 topology identity`
- [`f02ee35e59d2`](https://github.com/Entif-AI/Bilqis-MLX/commit/f02ee35e59d29372acd217c8f5ea62a7484cf034) `docs(bamf): bind successor gate and baseline custody`
- [`bd3a3ce0450c`](https://github.com/Entif-AI/Bilqis-MLX/commit/bd3a3ce0450c5f4b0b7f9aadade7db42c3ccc1bd) `feat(semantics): persist append-only atlas ABI`
- [`12b6b86ba51f`](https://github.com/Entif-AI/Bilqis-MLX/commit/12b6b86ba51f3cd927ff3aa6f369a62b232014c6) `feat(semantics): expose frozen atlas snapshot`
- [`f4da35cf5d0e`](https://github.com/Entif-AI/Bilqis-MLX/commit/f4da35cf5d0ee5dfec118c640a37b9031007a1da) `feat(runtime): stage BAMF tensor registry`
- [`bfa81d0071ea`](https://github.com/Entif-AI/Bilqis-MLX/commit/bfa81d0071ea2bd5d06cf2b0e55b56a2c7880fef) `feat(bamf): validate workstack and coordinate shared writers`
- [`ba9ec030a7af`](https://github.com/Entif-AI/Bilqis-MLX/commit/ba9ec030a7af8ad065d85b00985389bcde58ccc8) `fix(semantics): harden atlas admission boundaries`
- [`99667b8dc10b`](https://github.com/Entif-AI/Bilqis-MLX/commit/99667b8dc10b94fd3857ff5329c74ab96d78f52d) `docs(bamf): bind foundation witness to delivered contract`
- [`e5023e138e41`](https://github.com/Entif-AI/Bilqis-MLX/commit/e5023e138e41a85a304632ed9f5a87d9211e972c) `feat(runtime): dispatch isolated BAMF model factories`
- [`544a4fdd6816`](https://github.com/Entif-AI/Bilqis-MLX/commit/544a4fdd68161ca7f72bcb2b25304c7c0ba553a9) `feat(bamf): reconcile live owner contracts for handoff`
- [`10de2930f29d`](https://github.com/Entif-AI/Bilqis-MLX/commit/10de2930f29d2500309b49b9ba7d259dce3e42c3) `refactor(semantics): split atlas snapshot reader`
- [`adc85149686b`](https://github.com/Entif-AI/Bilqis-MLX/commit/adc85149686b09ccc552276d5ded7e083c7d6a99) `feat(semantics): add occurrence-aware frame records`
- [`3ff503bb6f7b`](https://github.com/Entif-AI/Bilqis-MLX/commit/3ff503bb6f7bf112d3c95fe6fdd6deecbaf27c6c) `feat(semantics): validate frame bindings`
- [`5e736aae9f71`](https://github.com/Entif-AI/Bilqis-MLX/commit/5e736aae9f717b2a5c166ef1f67db1911888ff35) `docs(bamf): record A01 EGM disposition`
- [`8b31bc049a2c`](https://github.com/Entif-AI/Bilqis-MLX/commit/8b31bc049a2cd4c365a0e96093e4230fbe32bd0c) `feat(semantics): bind released source frames`
- [`5b2e31b4e4a1`](https://github.com/Entif-AI/Bilqis-MLX/commit/5b2e31b4e4a1040aa705a1778ea1c7ad43ef12bc) `feat(bamf): prepare provisional released training batches`
- [`b378255cc16c`](https://github.com/Entif-AI/Bilqis-MLX/commit/b378255cc16c22cf4e5d14071f6789672a1607c3) `fix(semantics): name frame contract digest shape`
- [`91d62a563cee`](https://github.com/Entif-AI/Bilqis-MLX/commit/91d62a563cee69145c26911868c0d7da9f096f92) `feat(semantics): encode compact frame words`
- [`0a7f8e6b54b9`](https://github.com/Entif-AI/Bilqis-MLX/commit/0a7f8e6b54b91caa03fda7365cc1676312a1bf86) `fix(semantics): bind numeric source contract`
- [`9b9a2886d2c2`](https://github.com/Entif-AI/Bilqis-MLX/commit/9b9a2886d2c24452a7c7f813dd84b4a11f2c31de) `feat(semantics): add extended frame fallback`
- [`7439f0a44835`](https://github.com/Entif-AI/Bilqis-MLX/commit/7439f0a4483559f15da21e817fc7743a914126b8) `fix: numeric source authority validation`
- [`55bdffae4f63`](https://github.com/Entif-AI/Bilqis-MLX/commit/55bdffae4f638b7887f5933d5616c4dfea1246ce) `feat: bind codec sidecar identity`
- [`926385cbf708`](https://github.com/Entif-AI/Bilqis-MLX/commit/926385cbf7089a1bf1c7114ba55a210f7b008341) `feat: context eligibility gate`
- [`222fc9b10a51`](https://github.com/Entif-AI/Bilqis-MLX/commit/222fc9b10a513707d01dae674987a9c3b408f900) `docs: reconcile A03 review evidence`
- [`c69b3e2de079`](https://github.com/Entif-AI/Bilqis-MLX/commit/c69b3e2de07940da5bd114e0ba49468fe3eba852) `docs: A03 EGM pass`
- [`7895cea9b36e`](https://github.com/Entif-AI/Bilqis-MLX/commit/7895cea9b36e9b04ef085be2b0c3de4002cae257) `fix: bind context grants to evidence`
- [`4c422aab0c87`](https://github.com/Entif-AI/Bilqis-MLX/commit/4c422aab0c870279451e8dd084f17bd1641befb6) `fix: frame authority checks`
- [`5e84ffbc237d`](https://github.com/Entif-AI/Bilqis-MLX/commit/5e84ffbc237d335c937a85e3d9cba37052514cfd) `docs: record A03 EGM and clear static debt`
- [`cba2ae4100ff`](https://github.com/Entif-AI/Bilqis-MLX/commit/cba2ae4100ff7a8c9ab421e536735a0526de4b73) `docs: record A13 independent review`
- [`9e3ec5b019c0`](https://github.com/Entif-AI/Bilqis-MLX/commit/9e3ec5b019c0468e4be762540894ee45f4c31923) `fix: enforce schema validity before codec fallback`
- [`5581b2278b2e`](https://github.com/Entif-AI/Bilqis-MLX/commit/5581b2278b2e5692a3b3a539b5904f7870822452) `docs: record A04 codec EGM pass`
- [`712037632d1e`](https://github.com/Entif-AI/Bilqis-MLX/commit/712037632d1e6d8a2a327080b386848866aa3980) `docs: record A04 full EGM clearance`
- [`e6a9b30af619`](https://github.com/Entif-AI/Bilqis-MLX/commit/e6a9b30af6197fb86a93a2b208b9a4bc7099ff8c) `feat(bamf): add source-qualified pure cognitive operators`
- [`e8142ed84338`](https://github.com/Entif-AI/Bilqis-MLX/commit/e8142ed84338b80b929c729bee17da6451c6aad4) `fix(bamf): bind pure operators to source contracts`
- [`ab5ed833a4bb`](https://github.com/Entif-AI/Bilqis-MLX/commit/ab5ed833a4bb529cc153f0f2d9c0da98a5d14044) `fix(bamf): fail closed on missing native operator authority`
- [`f950944460f4`](https://github.com/Entif-AI/Bilqis-MLX/commit/f950944460f4c1b1e0878fb32d3f268cfb534601) `docs(bamf): record A07.1 independent EGM clearance`
- [`e959100c6b2f`](https://github.com/Entif-AI/Bilqis-MLX/commit/e959100c6b2f820c726cb6f73b86a2686eb704cb) `feat(bamf): expose approved context projections and formal envelopes`
- [`25928fc295da`](https://github.com/Entif-AI/Bilqis-MLX/commit/25928fc295dae402c8e3d3a91c7d0d23ff5a708d) `fix(bamf): authenticate formal source grants before admission`
- [`2aa6d127e913`](https://github.com/Entif-AI/Bilqis-MLX/commit/2aa6d127e91391830aad238be39160e10e00f053) `feat(bamf): isolate solver from evaluation gold and source cache`
- [`f4245d5edf68`](https://github.com/Entif-AI/Bilqis-MLX/commit/f4245d5edf681467ff24c0854b47158a7cecec69) `fix(bamf): attest formal row identity through source redraw`
- [`f351334ca4c3`](https://github.com/Entif-AI/Bilqis-MLX/commit/f351334ca4c3b25625edb09bf30b830a2c886827) `docs(bamf): record A13.2 independent EGM clearance`
- [`a02a64dde1c5`](https://github.com/Entif-AI/Bilqis-MLX/commit/a02a64dde1c501f9e06544bf75f80852a6a83b9d) `feat(bamf): add deterministic AtlasFeatures v2 projection`
- [`29f3d9bb1f9c`](https://github.com/Entif-AI/Bilqis-MLX/commit/29f3d9bb1f9c8e3b7c84b660e3b1e0d14aa2fc79) `feat(bamf): emit local C09 context invalidation receipts`
- [`819a6533ddb4`](https://github.com/Entif-AI/Bilqis-MLX/commit/819a6533ddb4eb8aafce85184e32daa6f19aa3a1) `fix(bamf): pin native operator dispatch to declared authority`
- [`dfe9e7f75647`](https://github.com/Entif-AI/Bilqis-MLX/commit/dfe9e7f75647589204a519356d4ede66d45f4682) `chore(bamf): clear new semantic static guard debt`
- [`9232a421c4ed`](https://github.com/Entif-AI/Bilqis-MLX/commit/9232a421c4edfc0556c77b56da40f58ac96440c9) `docs(bamf): record A07.2 independent EGM clearance`
- [`b9b38e2ddb64`](https://github.com/Entif-AI/Bilqis-MLX/commit/b9b38e2ddb64121bbaa24f0a06004e1951d58087) `feat(bamf): prepare provisional microbatches and delivery capture`
- [`1920f6c93123`](https://github.com/Entif-AI/Bilqis-MLX/commit/1920f6c931237022c5aebc56ee787891173e228b) `test(bamf): qualify provisional atomic modality dispatch`
- [`eca35a00df32`](https://github.com/Entif-AI/Bilqis-MLX/commit/eca35a00df329f680fe7d3c9d43156427ac197ec) `feat(runtime): qualify BAMF tensor registry custody`
- [`98c6e43cea16`](https://github.com/Entif-AI/Bilqis-MLX/commit/98c6e43cea16130cf240c14ad293e8c6f8d82088) `feat(bamf): preserve source families and resolve released rule policies`
- [`182fb4a67703`](https://github.com/Entif-AI/Bilqis-MLX/commit/182fb4a677034e95c7f9a232be4d16dc06cec23b) `feat(bamf): bind replay teacher to isolated successor epoch`
- [`6e8e6dedb606`](https://github.com/Entif-AI/Bilqis-MLX/commit/6e8e6dedb6065c7ac1d9160380b1046187246b31) `feat(bamf): isolate teacher evidence across geometry regions`
- [`9c8d60fb2533`](https://github.com/Entif-AI/Bilqis-MLX/commit/9c8d60fb25333315d305ac938fb0b56f1a0fa99e) `feat(runtime): reconcile exact BAMF parameter census`
- [`3d34dfc58856`](https://github.com/Entif-AI/Bilqis-MLX/commit/3d34dfc5885613585c6ad833f3cc516356e6e09f) `feat(bamf): gate read-only historical mentor evaluation`
- [`0bc58c840d9f`](https://github.com/Entif-AI/Bilqis-MLX/commit/0bc58c840d9fac703f41e5987b05a4e79a0f3de4) `feat(runtime): version BAMF generation extents and provenance`
- [`0b8380cd3abb`](https://github.com/Entif-AI/Bilqis-MLX/commit/0b8380cd3abbb471b70666865367bcb1bb9c027b) `feat(topology): establish BAMF v2 topology and custody foundations`
- [`fe6e4d15f123`](https://github.com/Entif-AI/Bilqis-MLX/commit/fe6e4d15f123a0735c3c038b068c0de2e8343320) `docs(runtime): verify historical state isolation for BAMF`
- [`edb1e9c48ddd`](https://github.com/Entif-AI/Bilqis-MLX/commit/edb1e9c48dddbcf1b39aee52fc347d7625a6dafc) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/bamf02-b-neural`
- [`f43ddfe21d2c`](https://github.com/Entif-AI/Bilqis-MLX/commit/f43ddfe21d2ccbafdf5705ae9cc373e942bda446) `fix(bamf): remove grade privileges from successor policy selection`
- [`a745e18f9c8d`](https://github.com/Entif-AI/Bilqis-MLX/commit/a745e18f9c8d4a5d26d49d1652f9e6eb9f54f3d7) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/bamf02-c-runtime`
- [`e40b19d037f2`](https://github.com/Entif-AI/Bilqis-MLX/commit/e40b19d037f2c05d18f0923f0a509ef9b71bad3a) `feat(runtime): convolve BAMF QKV with boundary-safe history`
- [`06cc296a7f62`](https://github.com/Entif-AI/Bilqis-MLX/commit/06cc296a7f62a52c142058e306399f11559e8800) `feat(runtime): add native BAMF grouped-query attention`
- [`158a852c7b75`](https://github.com/Entif-AI/Bilqis-MLX/commit/158a852c7b75c1e7184f01974af3e1ed906e091b) `feat(runtime): add BAMF causal convolution and native GQA`
- [`6e83c0f6618f`](https://github.com/Entif-AI/Bilqis-MLX/commit/6e83c0f6618f81a6d41f82503f16a80b8e14164f) `feat(runtime): implement Lane C runtime and delivery`
- [`982ba51127b7`](https://github.com/Entif-AI/Bilqis-MLX/commit/982ba51127b7e851cd795039644565bc3625ebaa) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/bamf02-a-semantics`
- [`335f79262d88`](https://github.com/Entif-AI/Bilqis-MLX/commit/335f79262d8807e559daf94a48ae3d3fa7fe78fa) `fix(bamf): source-attest A06 factor maps and root senses`
- [`d23c5999e278`](https://github.com/Entif-AI/Bilqis-MLX/commit/d23c5999e2783a99617871dc69a1484d764d7011) `fix(bamf): validate C09 invalidation record boundaries`
- [`9265f00ce482`](https://github.com/Entif-AI/Bilqis-MLX/commit/9265f00ce482b033ff0db2c31e0d951e7e3ebc2d) `fix(bamf): bind Atlas feature schemas to released source dialects`
- [`c712a92a773c`](https://github.com/Entif-AI/Bilqis-MLX/commit/c712a92a773cf67e93cf757dc0caa242a0eb042c) `docs(bamf): record A13.3 independent EGM clearance`
- [`5bc6faa4a4ee`](https://github.com/Entif-AI/Bilqis-MLX/commit/5bc6faa4a4ee7faf151d8769d21178d7f4609727) `fix(bamf): close Atlas overflow and collision proof gaps`
- [`b3bea14fe241`](https://github.com/Entif-AI/Bilqis-MLX/commit/b3bea14fe241f5f11c68d11a41af3d938aebd8ae) `fix(bamf): protect C09 context transitions`
- [`caedd9eaeeda`](https://github.com/Entif-AI/Bilqis-MLX/commit/caedd9eaeedab578dd9ad4899eea10aa8536d4d3) `docs(bamf): record full A06.1 and A13.3 EGM clearance`
- [`4a5800e0f37a`](https://github.com/Entif-AI/Bilqis-MLX/commit/4a5800e0f37ae1a40107d60772aa18d8c8b2a0e6) `feat(bamf): publish immutable local AtlasFeatures and reference vectors`
- [`a4be8062988e`](https://github.com/Entif-AI/Bilqis-MLX/commit/a4be8062988e84b3f0a053dbc5067e44471ff89d) `fix(bamf): enforce Atlas feature successor lineage on export`
- [`1b16a1ee399c`](https://github.com/Entif-AI/Bilqis-MLX/commit/1b16a1ee399c9c1ac0d6a9c48fba4a0e946ee720) `docs(bamf): record A06.2 independent EGM clearance`
- [`7cd02597fe87`](https://github.com/Entif-AI/Bilqis-MLX/commit/7cd02597fe871649c7090b8d42a337aee9a88fea) `feat(bamf): execute bounded source-qualified compositional DAGs`
- [`ab326694835a`](https://github.com/Entif-AI/Bilqis-MLX/commit/ab326694835a1dc46b646fdfca07a3b6c3eb2477) `style(bamf): normalize DAG module EOF`
- [`e0ba6555e542`](https://github.com/Entif-AI/Bilqis-MLX/commit/e0ba6555e542518898d445f48746e9584c369da2) `fix(bamf): filter DAG hole choices by source-visible applicability`
- [`88621bce14e5`](https://github.com/Entif-AI/Bilqis-MLX/commit/88621bce14e5d07ac1bf725ffe700b2d26801e28) `fix(bamf): bind DAG memo to consulted sources and count deferred lookups`
- [`f09b3e572185`](https://github.com/Entif-AI/Bilqis-MLX/commit/f09b3e572185ec304158cd3de17ba8f691204a68) `docs(bamf): record A07.3 EGM findings and repaired head`
- [`6b7f4daaf892`](https://github.com/Entif-AI/Bilqis-MLX/commit/6b7f4daaf89293f5a12a1381e016d01e877128f4) `fix(bamf): prove unique DAG hole bindings and reject poisoned memo`
- [`fadbe6841402`](https://github.com/Entif-AI/Bilqis-MLX/commit/fadbe684140220776f906627a1c4ec28b41ba216) `docs(bamf): reconcile A07.3 second EGM findings`
- [`d0fd5ab5a758`](https://github.com/Entif-AI/Bilqis-MLX/commit/d0fd5ab5a7586ce57f1b14cf767acf448145a584) `feat(bamf): index direct correction dependencies and lazy holds`
- [`07249116fe9e`](https://github.com/Entif-AI/Bilqis-MLX/commit/07249116fe9e3cf72fefecf0bab4abbae9007cbf) `docs(bamf): record C09.1 scoped candidate evidence`
- [`be7127151d39`](https://github.com/Entif-AI/Bilqis-MLX/commit/be7127151d3933db5a87519fe55410edf0311f7a) `feat(bamf): preserve correction branches and requalify learned support`
- [`7353176b18ce`](https://github.com/Entif-AI/Bilqis-MLX/commit/7353176b18ce16ce0cdb678ddb9e06806b094639) `docs(bamf): record C09.2 provisional source-requalification evidence`
- [`84bba19cd002`](https://github.com/Entif-AI/Bilqis-MLX/commit/84bba19cd00206f6d3fa55f76c23866f584315c8) `feat(bamf): compile causal append-only partial frame prefixes`
- [`1b7d797a4bd9`](https://github.com/Entif-AI/Bilqis-MLX/commit/1b7d797a4bd97275b0662a93155e69c7cdb24b5c) `feat(bamf): bind as-of validity and escalate stale remediation replay`
- [`053f6f48c22b`](https://github.com/Entif-AI/Bilqis-MLX/commit/053f6f48c22be9b3aa5b742fc5cf975d8e1a71a3) `docs(bamf): record C09.3 temporal and process-fault evidence`
- [`e4317684e858`](https://github.com/Entif-AI/Bilqis-MLX/commit/e4317684e8589324ad2ceb0011eca1d50f0180c5) `docs(bamf): record A05.1 pushed implementation and PR linkage`
- [`8065c52ee2c4`](https://github.com/Entif-AI/Bilqis-MLX/commit/8065c52ee2c4cd4436fa92a3d0ddf7f5599036c7) `feat(bamf): map source positions and isolate padded prefix rows`
- [`df8fd4fd6d9e`](https://github.com/Entif-AI/Bilqis-MLX/commit/df8fd4fd6d9e0d2638740f7ba4acc10719e06aa0) `feat(bamf): plan topology-aware microbatches and weighted gradient step`
- [`a4f76fcdcf9b`](https://github.com/Entif-AI/Bilqis-MLX/commit/a4f76fcdcf9b582ae03a973a4f94b65fc3cad982) `docs(bamf): record A05.2 pushed maps and PR linkage`
- [`b5ed35f5d1ae`](https://github.com/Entif-AI/Bilqis-MLX/commit/b5ed35f5d1aebb8d7ad73eb7e55820d58954b0b8) `docs(bamf): record C08.1 resource-plan evidence`
- [`198fbe6d75ae`](https://github.com/Entif-AI/Bilqis-MLX/commit/198fbe6d75aebb7c61b125faac778fe64b498393) `feat(bamf): snapshot MLX memory and restore before bounded OOM retry`
- [`10da73107453`](https://github.com/Entif-AI/Bilqis-MLX/commit/10da73107453e68dc3633d1d12727b386d94d6b7) `docs(bamf): record C08.2 MLX API and OOM recovery evidence`
- [`3209c1f03363`](https://github.com/Entif-AI/Bilqis-MLX/commit/3209c1f033630b903f00d82aa78bb96cb50e2d5e) `feat(bamf): freeze CPU source packets and guard next-bundle disk reserve`
- [`b3de93862dca`](https://github.com/Entif-AI/Bilqis-MLX/commit/b3de93862dca64172a3aa7c1fdec9d806ce83856) `docs(bamf): record C08.3 CPU and disk reserve evidence`
- [`a9e55fb3e993`](https://github.com/Entif-AI/Bilqis-MLX/commit/a9e55fb3e993c035655dd19ccf8b3110443c035e) `feat(bamf): isolate hidden targets and enforce lawful 1024-position segments`
- [`e1b45f038062`](https://github.com/Entif-AI/Bilqis-MLX/commit/e1b45f0380628500b33d1ddad9dc55597f9db25e) `docs(bamf): record A05.3 pushed implementation and PR linkage`
- [`3d34d70e5eb9`](https://github.com/Entif-AI/Bilqis-MLX/commit/3d34d70e5eb9da9e683f85c6fa398209ccda8044) `fix(bamf): validate prefix ordering and approved occurrence boundaries`
- [`43da1b80ea41`](https://github.com/Entif-AI/Bilqis-MLX/commit/43da1b80ea410bf0033716225648ce8921b6006a) `docs(bamf): record A05.3 post-candidate boundary hardening`
- [`cd3ec533a823`](https://github.com/Entif-AI/Bilqis-MLX/commit/cd3ec533a823eea3bd407d5e9ac13c87cfb42230) `fix(bamf): verify source signatures and transitive correction safety`
- [`9ad2dca69c1f`](https://github.com/Entif-AI/Bilqis-MLX/commit/9ad2dca69c1fc8824661338619ab248a81dacb82) `docs(bamf): record C09 EGM findings and authority repairs`
- [`63583b62d04a`](https://github.com/Entif-AI/Bilqis-MLX/commit/63583b62d04a7c1d9e8c632e6026fd4f8e6a8eea) `test(bamf): prove inclusive 1024 neural-position boundary`
- [`e20003a55115`](https://github.com/Entif-AI/Bilqis-MLX/commit/e20003a5511562212d33371e9cf54eb26839cf9d) `feat(bamf): append-only Akasha outbox with C09 source intents`
- [`90f72c9172a1`](https://github.com/Entif-AI/Bilqis-MLX/commit/90f72c9172a1b6b70279d73b8e3d555122920b7f) `docs(bamf): record C10.1 append-only outbox evidence`
- [`f79001cf04a0`](https://github.com/Entif-AI/Bilqis-MLX/commit/f79001cf04a07e183a961049c91ae38c2b30e8f1) `feat(bamf): bind Akasha outbox views to source and rights domains`
- [`6b5460032fc0`](https://github.com/Entif-AI/Bilqis-MLX/commit/6b5460032fc0b19115843cce95fe8be9582af141) `integrate(bamf): merge reviewed Lane A cut through A07.3`
- [`584b33b4f32e`](https://github.com/Entif-AI/Bilqis-MLX/commit/584b33b4f32ebb52c9413c6fdab4ac1285e2cdc0) `docs(bamf): record C10.2 domain projection evidence`
- [`59f89ffc98b1`](https://github.com/Entif-AI/Bilqis-MLX/commit/59f89ffc98b1f91f61c0f8d2aa42a69a90a7d0cf) `feat(bamf): stage private-safe Akasha projections before atomic promotion`
- [`8fe6f260069a`](https://github.com/Entif-AI/Bilqis-MLX/commit/8fe6f260069a2c4a6beb17c2b600545fed031a46) `docs(bamf): record C10.3 staging and privacy evidence`
- [`fc91591641ad`](https://github.com/Entif-AI/Bilqis-MLX/commit/fc91591641ad679a792944cc2d3e4dd61eb279cc) `feat(bamf): bind attention view to exact B01 tensor ledger`
- [`8ee79c23ec7e`](https://github.com/Entif-AI/Bilqis-MLX/commit/8ee79c23ec7e88b7915bc185e8c5c61ccc7fce79) `fix(bamf): bind revalidation to correction and pairwise authority scopes`
- [`d2d8f68b4b73`](https://github.com/Entif-AI/Bilqis-MLX/commit/d2d8f68b4b738fead88187cb4ab20a8bf73653f7) `docs(bamf): record B04.3 independent EGM pass`
- [`d7792048a7f9`](https://github.com/Entif-AI/Bilqis-MLX/commit/d7792048a7f9106bc155aed967c15e08c84de7f3) `docs(bamf): record C09 correction-bound EGM repairs`
- [`ecc4b7656dc3`](https://github.com/Entif-AI/Bilqis-MLX/commit/ecc4b7656dc3f2ff7a806fe71c151d86efb8840c) `merge: refresh Lane C from reviewed unified baseline`
- [`5b2b64035f37`](https://github.com/Entif-AI/Bilqis-MLX/commit/5b2b64035f37f7e30174ed08b0ad27734bc72e9a) `docs(bamf): record B04.4 independent EGM pass`
- [`39c1d95a708f`](https://github.com/Entif-AI/Bilqis-MLX/commit/39c1d95a708f12baf25b8cff3bb8750ca61def7d) `feat(bamf): route source-qualified exact cache and neural DAG solves`
- [`9b8bd9c6ca76`](https://github.com/Entif-AI/Bilqis-MLX/commit/9b8bd9c6ca768a4c3efcab950f754d8b6287f631) `docs(bamf): record C04.1 source-qualified solver evidence`
- [`d5a5885a6a08`](https://github.com/Entif-AI/Bilqis-MLX/commit/d5a5885a6a087f3ac6fcad41abdcc7bd47ab66c7) `feat(bamf): bound local refinements and safe neural fallback`
- [`7cb35bf7b97b`](https://github.com/Entif-AI/Bilqis-MLX/commit/7cb35bf7b97b784f7a99839add57b1d195fe4307) `docs(bamf): record C04.2 bounded fallback evidence`
- [`7f40b3ac1a48`](https://github.com/Entif-AI/Bilqis-MLX/commit/7f40b3ac1a48839d46abb526959d7d153d3421c8) `feat(bamf): stage source-ordered depth selector and residual gate`
- [`270ef7c9f908`](https://github.com/Entif-AI/Bilqis-MLX/commit/270ef7c9f90870ba11449ecf7bd24e76a3266cbe) `feat(bamf): stage exact B01 depth selector tensor view`
- [`07276949c17d`](https://github.com/Entif-AI/Bilqis-MLX/commit/07276949c17d4ea1a739c767a6e4a99ac16e110f) `test(bamf): prove gradients reach all depth source states`
- [`c8bf2338181e`](https://github.com/Entif-AI/Bilqis-MLX/commit/c8bf2338181ee5bc1a6048588c31c830ced01914) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/bamf02-a-semantics`
- [`d86cb7762496`](https://github.com/Entif-AI/Bilqis-MLX/commit/d86cb7762496dc53b28a011820a801be45904bd1) `fix(bamf): seal depth tensor ownership and reject nonfinite inputs`
- [`b62df3019d7e`](https://github.com/Entif-AI/Bilqis-MLX/commit/b62df3019d7e1b77c1c0f366460efe1d803c49f3) `perf(bamf): batch finite validation into one MLX evaluation`
- [`de5bb9c56299`](https://github.com/Entif-AI/Bilqis-MLX/commit/de5bb9c562992e3620a539dc5519f26a7374e772) `fix(bamf): bind raw atoms and lawful segments to source grants`
- [`3c1a10971cc0`](https://github.com/Entif-AI/Bilqis-MLX/commit/3c1a10971cc02362b499f6c74b79f10c717006e9) `docs(bamf): record combined B01 B04 B05 MLX proof`
- [`d1067b16f476`](https://github.com/Entif-AI/Bilqis-MLX/commit/d1067b16f4765bfc27344680bcca52141645a975) `docs(bamf): record depth finite-check latency caveat`
- [`ea89131c29e1`](https://github.com/Entif-AI/Bilqis-MLX/commit/ea89131c29e1de099b2699bf24517570bf45554e) `wip(bamf): source-family census candidate for A08.1a`
- [`5c18e871f5f5`](https://github.com/Entif-AI/Bilqis-MLX/commit/5c18e871f5f51f770687c9e1e7910536a4430819) `feat(bamf): bind full Atlas census to A08 curriculum owner API`
- [`2a925c42d8c9`](https://github.com/Entif-AI/Bilqis-MLX/commit/2a925c42d8c9fc02ffdb522ed6aba400c078d55e) `docs(bamf): record independent A05 EGM clearance`
- [`9c61119c5631`](https://github.com/Entif-AI/Bilqis-MLX/commit/9c61119c563175e9e85e8499b3088aad44b31718) `feat(bamf): stage source-attested constructive identity lessons`
- [`0d4ae8ab245c`](https://github.com/Entif-AI/Bilqis-MLX/commit/0d4ae8ab245c3f0de2f9b7ed609981309f4c04aa) `fix(bamf): report only exercised source variation axes`
- [`2442ae78684d`](https://github.com/Entif-AI/Bilqis-MLX/commit/2442ae78684d5f695ed2e430ffbdc76db6490f7d) `fix(bamf): require formal source authority for family census`
- [`915e22a884e0`](https://github.com/Entif-AI/Bilqis-MLX/commit/915e22a884e09b2d981b55378d749db177c1ee8b) `docs(bamf): recursively decompose A08 constructive families`
- [`8a4777da7ba8`](https://github.com/Entif-AI/Bilqis-MLX/commit/8a4777da7ba8bb55dade1c3e93f8fb159be3c9d5) `Merge remote-tracking branch 'origin/codex/bamf02-b-neural' into codex/bamf02-b-neural`
- [`050b4f648b0f`](https://github.com/Entif-AI/Bilqis-MLX/commit/050b4f648b0fce9eda1051d988b4f4cf30dec3ef) `fix(runtime): preserve task bindings and shared solve budget`
- [`ae2faa1e78d8`](https://github.com/Entif-AI/Bilqis-MLX/commit/ae2faa1e78d813ae753256b14d42670277d7004a) `fix(bamf): require pinned A01 artifact for A08 source census`
- [`8e88d1474be6`](https://github.com/Entif-AI/Bilqis-MLX/commit/8e88d1474be67d94f563a378ce1f74919fbcb50c) `feat(runtime): record provenance-safe solver replay`
- [`f8b90c185d6f`](https://github.com/Entif-AI/Bilqis-MLX/commit/f8b90c185d6fffa522ecd90d10ddd96e6a4359e6) `fix(bamf): anchor A08 source authority to governed A01 pins`
- [`2cd16cba3ef5`](https://github.com/Entif-AI/Bilqis-MLX/commit/2cd16cba3ef5c1c2feab74fc3843c4b1ea96948a) `feat(learning): stage source-bound factorized embeddings`
- [`ae8c86a8939c`](https://github.com/Entif-AI/Bilqis-MLX/commit/ae8c86a8939c38ed7b4eaf976badd065e34e0e52) `feat(runtime): assess paired complete-solver capabilities`
- [`0d638ee17414`](https://github.com/Entif-AI/Bilqis-MLX/commit/0d638ee1741433a309cea1c79f4feb886445f688) `fix(bamf): separate unverified projections from A01 attestation`
- [`0f1eada013b6`](https://github.com/Entif-AI/Bilqis-MLX/commit/0f1eada013b6f557983ed371fcd1bc6d22070146) `test(bamf): assert unverified schemas cannot claim source authority`
- [`da6ba6f4c8ce`](https://github.com/Entif-AI/Bilqis-MLX/commit/da6ba6f4c8ce8ca6428646cb820762270dd0ac3d) `Revert "test(bamf): assert unverified schemas cannot claim source authority"`
- [`4e166b083028`](https://github.com/Entif-AI/Bilqis-MLX/commit/4e166b08302878c0ca86d0a2dfda245cbdfdff09) `Revert "fix(bamf): separate unverified projections from A01 attestation"`
- [`cd84caed7580`](https://github.com/Entif-AI/Bilqis-MLX/commit/cd84caed7580d9b6dcc5d02d1a9bff7f82497f7b) `feat(learning): preserve complete-solver title and mastery evidence`
- [`a5b5febd0f39`](https://github.com/Entif-AI/Bilqis-MLX/commit/a5b5febd0f390a7e908b4e6afd7cc7f5d167f22a) `feat(learning): stage deterministic row proposals and masked loss`
- [`c78bde8fdfa4`](https://github.com/Entif-AI/Bilqis-MLX/commit/c78bde8fdfa4ea5d6ab6b68f9e7a9e7beaf878dd) `fix(bamf): revalidate source proposals at every consuming boundary`
- [`96ae15bdc2ad`](https://github.com/Entif-AI/Bilqis-MLX/commit/96ae15bdc2ad098b428c6161c9a33d07cc537f35) `fix(bamf): compare source proposals by strict canonical bytes`
- [`807a9b877cd8`](https://github.com/Entif-AI/Bilqis-MLX/commit/807a9b877cd8b2aeb5acefdae837c4f452ba255f) `feat(learning): validate embedding registry and update coverage`
- [`aa3a9e288177`](https://github.com/Entif-AI/Bilqis-MLX/commit/aa3a9e288177862bf0200bdf209a1164048692c5) `feat(runtime): preserve historical evidence and uniform authority gates`
- [`e3aea466fbe4`](https://github.com/Entif-AI/Bilqis-MLX/commit/e3aea466fbe45e287dc0efe030956cf26505845c) `Merge branch 'codex/bamf02-b05-candidate-20261029' into codex/bamf02-b-neural`
- [`f3b8ae13cce6`](https://github.com/Entif-AI/Bilqis-MLX/commit/f3b8ae13cce6bdc42ba42bdb44877df33333e0a7) `fix(runtime): bind depth features to released source members`
- [`e63b64297ef8`](https://github.com/Entif-AI/Bilqis-MLX/commit/e63b64297ef839d27032d4e9c92398ad2e61e49a) `feat(bamf): stage A03-shaped motif keys and candidate allocation`
- [`19cad90e0ec1`](https://github.com/Entif-AI/Bilqis-MLX/commit/19cad90e0ec121ef54b795c3680694c28f0da837) `fix(bamf): bind child occurrence identity in exact motif keys`
- [`c09c1ff9156c`](https://github.com/Entif-AI/Bilqis-MLX/commit/c09c1ff9156c6a22cf74b72a6bd835c29667c8b8) `fix(bamf): abstract child relation and accept optional empty frames`
- [`5beb52be3826`](https://github.com/Entif-AI/Bilqis-MLX/commit/5beb52be38268c28deeb826ed274a5dc22229f75) `feat(bamf): stage bounded motif page growth and seeded rows`
- [`5e0204668096`](https://github.com/Entif-AI/Bilqis-MLX/commit/5e020466809619debbad8a6349928d87f99e004f) `feat(bamf): gate motif plans on A03 and A13 source authority`
- [`434b8e029597`](https://github.com/Entif-AI/Bilqis-MLX/commit/434b8e0295972049f11769e3614fe38d4566505f) `feat(bamf): stage B01-authoritative motif parameter view`
- [`021307fb5fa0`](https://github.com/Entif-AI/Bilqis-MLX/commit/021307fb5fa0ebd3b0c674f810ef82ebd399b44b) `docs(bamf): record B07 review and quarantine source probe`
- [`3743318e9360`](https://github.com/Entif-AI/Bilqis-MLX/commit/3743318e9360c5c9ce8d4f18915896a29b770b59) `fix(bamf): isolate motif parameter reads from write-through`
- [`7b773f21addd`](https://github.com/Entif-AI/Bilqis-MLX/commit/7b773f21adddea5db86605068d69885887bf882f) `docs(bamf): record B07.4 independent EGM clearance`
- [`463edaf78b5f`](https://github.com/Entif-AI/Bilqis-MLX/commit/463edaf78b5fe4bae81d42ce4b04df30f0c02731) `feat(engram): work on Atlas Engram (B07.1)`
- [`2a492ce38561`](https://github.com/Entif-AI/Bilqis-MLX/commit/2a492ce385618b0bfd5614bbfe99440e4f6c8ef0) `feat(skos): curriculum SKOS work (A08.1)`
- [`7afdc0c95ba6`](https://github.com/Entif-AI/Bilqis-MLX/commit/7afdc0c95ba68a32df33faedb288f6155c7b8d34) `feat(runtime): work on cognitive solver`
- [`8d91def60223`](https://github.com/Entif-AI/Bilqis-MLX/commit/8d91def60223eaf218f1cb4fc26e7bab5a12a117) `merge: reconcile local C04 replay work with reviewed Lane C`
- [`84a10e907607`](https://github.com/Entif-AI/Bilqis-MLX/commit/84a10e9076074b158c44e287a776d67532c34712) `docs(bamf): record scoped B07 intake and combined proof`
- [`4ed04559c4e1`](https://github.com/Entif-AI/Bilqis-MLX/commit/4ed04559c4e13d6ddc135192e312645ef755b7e9) `Merge branch 'codex/bamf02-a-semantics' into codex/bamf02-a08-authority-final-20261029`
- [`1f306567d474`](https://github.com/Entif-AI/Bilqis-MLX/commit/1f306567d4740204b4b429c8f2903a2b0a9be576) `fix(bamf): enforce exact A01 source selection and lesson evidence`
- [`12c6545edcec`](https://github.com/Entif-AI/Bilqis-MLX/commit/12c6545edcec8e1e74f05ebef583e31a162ab83f) `feat(encoder): implement provisional source-bound frame pass`
- [`9afa1f9ed4c9`](https://github.com/Entif-AI/Bilqis-MLX/commit/9afa1f9ed4c94480837ba1ac0fd243287606cf3e) `feat(bamf): independently check source identity and attested relations`
- [`bcabe0b35fa3`](https://github.com/Entif-AI/Bilqis-MLX/commit/bcabe0b35fa38199c22d88e955327fa0daf22ccf) `feat(bamf): source-bind formal operators without granting execution`
- [`e4bd19854c54`](https://github.com/Entif-AI/Bilqis-MLX/commit/e4bd19854c548e640115c752d0786f7f35a8b440) `fix(bamf): distinguish formal source projections from attestation`
- [`2ee915dc8ba8`](https://github.com/Entif-AI/Bilqis-MLX/commit/2ee915dc8ba87451c0cdaf1ed45d0434a309004e) `fix(bamf): require source replay for formal operator proposals`
- [`91d80e088611`](https://github.com/Entif-AI/Bilqis-MLX/commit/91d80e088611b10b292a32568f4198b17b99ef35) `fix(bamf): reject formal source proposal equality spoofing`
- [`99a0f37e45cd`](https://github.com/Entif-AI/Bilqis-MLX/commit/99a0f37e45cd82176d0950e311bf55355e25abaa) `feat(learning): derive verified ordinal salience and head logits`
- [`bce4b8792134`](https://github.com/Entif-AI/Bilqis-MLX/commit/bce4b879213445249703e20d8cf43bab11f1e9e6) `feat(encoder): preserve approved atomic fallback vectors`
- [`74be2874bd6a`](https://github.com/Entif-AI/Bilqis-MLX/commit/74be2874bd6a4f4163878ebc547e2cfabde890e4) `docs: record A08 EGM clearance`
- [`816209665714`](https://github.com/Entif-AI/Bilqis-MLX/commit/81620966571418d8546d1f0d9169c58e0363da66) `feat(refinement): implement bounded shared recurrence kernel`
- [`ac498099b56a`](https://github.com/Entif-AI/Bilqis-MLX/commit/ac498099b56a38f3b669e16d30f8bab580709f49) `feat(bamf): implement Lane A semantic atlas and curricula`
- [`5a2d84104e9b`](https://github.com/Entif-AI/Bilqis-MLX/commit/5a2d84104e9bd20bfeba90d2e374069ebccb1573) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/bamf02-b-neural`
- [`867aaa34fb16`](https://github.com/Entif-AI/Bilqis-MLX/commit/867aaa34fb16e0a2e28d58f8e77d5af11670402b) `feat(bamf): task-scoped formal lessons with A13 rights replay`
- [`9cf57b94c176`](https://github.com/Entif-AI/Bilqis-MLX/commit/9cf57b94c17647cf74fe47d7557bfff03c8db02a) `Merge branch 'codex/bamf02-a-semantics' into codex/bamf02-a08-formal-final-20261029`
- [`3b0004c30e19`](https://github.com/Entif-AI/Bilqis-MLX/commit/3b0004c30e19b39f877b68db69f12ee7d5f22b92) `Merge branch 'codex/bamf02-a-semantics' into codex/bamf02-a08-formal-final-20261029`
- [`d97f648633d4`](https://github.com/Entif-AI/Bilqis-MLX/commit/d97f648633d4a117a68c244bfa2f93e497c07900) `feat(bamf): bind attention view to exact B01 tensor ledger`
- [`776a03dcd5d1`](https://github.com/Entif-AI/Bilqis-MLX/commit/776a03dcd5d1a7c2d87f98ac5e90cc33060b7660) `docs(bamf): record B04.3 independent EGM pass`
- [`4a1a61121279`](https://github.com/Entif-AI/Bilqis-MLX/commit/4a1a61121279fabcf43dd8840ef998be4a8c899e) `docs(bamf): record B04.4 independent EGM pass`
- [`bb4b11594eba`](https://github.com/Entif-AI/Bilqis-MLX/commit/bb4b11594eba97249e8d26b99c8d6056f8e337bd) `feat(bamf): route source-qualified exact cache and neural DAG solves`
- [`9e0f509cef52`](https://github.com/Entif-AI/Bilqis-MLX/commit/9e0f509cef52b710d3b4450f637aacd0acdb9a65) `docs(bamf): record C04.1 source-qualified solver evidence`
- [`b45931d7140d`](https://github.com/Entif-AI/Bilqis-MLX/commit/b45931d7140d6f964e31e71a63d4094c25893cae) `feat(bamf): bound local refinements and safe neural fallback`
- [`25b4b7688a07`](https://github.com/Entif-AI/Bilqis-MLX/commit/25b4b7688a0764980245c604d66bfaf5c76ab23c) `docs(bamf): record C04.2 bounded fallback evidence`
- [`9c6400379799`](https://github.com/Entif-AI/Bilqis-MLX/commit/9c64003797995e2f0303877f1db9bd666376bcd7) `fix(runtime): preserve task bindings and shared solve budget`
- [`904ab351af9b`](https://github.com/Entif-AI/Bilqis-MLX/commit/904ab351af9bfceadbf5a417dfe46dcc9fb495a8) `feat(runtime): record provenance-safe solver replay`
- [`ef710a849d77`](https://github.com/Entif-AI/Bilqis-MLX/commit/ef710a849d776fe13a6ac78e0d0b575a8f82b38f) `feat(runtime): assess paired complete-solver capabilities`
- [`388a1b0902ca`](https://github.com/Entif-AI/Bilqis-MLX/commit/388a1b0902ca6feb1604ae36b63d40fb28620389) `feat(learning): preserve complete-solver title and mastery evidence`
- [`757324c7b32f`](https://github.com/Entif-AI/Bilqis-MLX/commit/757324c7b32fb45776c991ddc5c9a76604da393b) `feat(runtime): preserve historical evidence and uniform authority gates`
- [`5daee1284bbc`](https://github.com/Entif-AI/Bilqis-MLX/commit/5daee1284bbce7461a104e2dfdadc0d646504daf) `chore(bamf): normalize C05.3 integration whitespace`
- [`13cf945bcc1a`](https://github.com/Entif-AI/Bilqis-MLX/commit/13cf945bcc1ab1449608b198534475302e030a2a) `fix(bamf): reject mutated formal typed values`
- [`09def57ae1a0`](https://github.com/Entif-AI/Bilqis-MLX/commit/09def57ae1a049886f2e7278543f86d28182021a) `feat(encoder): consume source-revalidated A05 rows`
- [`2b43acd80b42`](https://github.com/Entif-AI/Bilqis-MLX/commit/2b43acd80b42b3138c599c1a52809115704ba425) `chore(bamf): merge reviewed B04.3/B04.4 cut`
- [`7ad8f8abc9ef`](https://github.com/Entif-AI/Bilqis-MLX/commit/7ad8f8abc9efcc4b9fb5311a1572979c49b22cf4) `chore(bamf): merge reviewed C04+C05 cut`
- [`ecbb788ff5db`](https://github.com/Entif-AI/Bilqis-MLX/commit/ecbb788ff5dbead7c02c38d192eef5d8c92911a3) `fix(bamf): revalidate formal lesson authority on check`
- [`d93e9587dfd5`](https://github.com/Entif-AI/Bilqis-MLX/commit/d93e9587dfd5ccb6d6895d8556ddb13b39b56299) `chore(bamf): merge reviewed unified A05 A08 and B04 work`
- [`a2644457be34`](https://github.com/Entif-AI/Bilqis-MLX/commit/a2644457be343f51925f154853043444bc121ff0) `docs: record scoped formal lesson EGM clearance`
- [`81f9954277c0`](https://github.com/Entif-AI/Bilqis-MLX/commit/81f9954277c035d0e524e5304876bc49ca69d030) `feat(encoder): support source-verified empty and atomic closures`
- [`9fa752b6410c`](https://github.com/Entif-AI/Bilqis-MLX/commit/9fa752b6410c8248aa784a361247a8a7230fb748) `Merge branch 'codex/bamf02-a-semantics' into codex/bamf02-a08-formal-final-20261029`
- [`94c81710ee5c`](https://github.com/Entif-AI/Bilqis-MLX/commit/94c81710ee5c1209d0358ee886b881d62f5f77a2) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/bamf02-b-neural`
- [`7020cd52f62f`](https://github.com/Entif-AI/Bilqis-MLX/commit/7020cd52f62ff75d15cfd37f50bd172359711237) `feat(learning): bind salience priority to replay teacher and local history`
- [`23cd0e97ed3c`](https://github.com/Entif-AI/Bilqis-MLX/commit/23cd0e97ed3c9543e4c279406abca5bb5c77bdd5) `feat(learning): aggregate independent salience patterns as conjectures`
- [`7b70b0d4f70c`](https://github.com/Entif-AI/Bilqis-MLX/commit/7b70b0d4f70c2df7d79ddd69db91a2eaf1da78ae) `fix(tests): support Python 3.14 immutable-field errors`
- [`b04c4181245c`](https://github.com/Entif-AI/Bilqis-MLX/commit/b04c4181245cb23f7f52f17735618125dde35af3) `feat(diagnostics): expose separate salience priority and recovery evidence`
- [`529e7f2212eb`](https://github.com/Entif-AI/Bilqis-MLX/commit/529e7f2212ebaef0bb51ac53cad5ec70e3e06f16) `feat(bamf): stage B06 prediction-local refinement policy`
- [`f6127211b1d2`](https://github.com/Entif-AI/Bilqis-MLX/commit/f6127211b1d2b882144eabc8eda88bd93457d8f3) `fix(bamf): permit two passes for declared unresolved nested queries`
- [`40c6b1694205`](https://github.com/Entif-AI/Bilqis-MLX/commit/40c6b1694205c566b7fc93e9cad59f6616934c05) `fix(bamf): bind refinement quota to A05 and train zero-pass route`
- [`9609256fe536`](https://github.com/Entif-AI/Bilqis-MLX/commit/9609256fe536d4f512f5a700a63212489d260ea1) `fix(bamf): require source-granted complete prefix inventory`
- [`242972c99bba`](https://github.com/Entif-AI/Bilqis-MLX/commit/242972c99bbac7f65dbe1d3f524c11bac5c6797c) `feat(bamf): stage copy-on-write motif allocation transactions`
- [`ea94f9e381f5`](https://github.com/Entif-AI/Bilqis-MLX/commit/ea94f9e381f5bd67a2b8b60a5556e6ee05b335a2) `fix(diagnostics): preserve fresh teacher and runtime import order`
- [`357aa3a136b0`](https://github.com/Entif-AI/Bilqis-MLX/commit/357aa3a136b091107f908f7c821cceed72832e41) `docs(bamf): preserve raw import failure without whitespace debt`
- [`82577b8ceb59`](https://github.com/Entif-AI/Bilqis-MLX/commit/82577b8ceb59f831142121058783851e8d2de9da) `docs(bamf): record B06.2 independent EGM pass`
- [`cac4c6f3d782`](https://github.com/Entif-AI/Bilqis-MLX/commit/cac4c6f3d782d32d3a0836c4159362bddc657803) `docs(bamf): record B07.3 scoped EGM pass`
- [`ead92a6b18b0`](https://github.com/Entif-AI/Bilqis-MLX/commit/ead92a6b18b03ae98f549118cfc361d13f33b6b4) `feat(runtime): persist provisional Atlas leases and stage unleased proposals`
- [`8ba5b8ae3c24`](https://github.com/Entif-AI/Bilqis-MLX/commit/8ba5b8ae3c24221ab3e317a805ffcce62baa7b37) `feat(bamf): stage rank-eight adapters and FAST row ages`
- [`baf859c86e29`](https://github.com/Entif-AI/Bilqis-MLX/commit/baf859c86e292ab5f1099cd574219f8faf0c29fb) `docs(bamf): record B09.1a scoped EGM pass`
- [`05ec82ec829b`](https://github.com/Entif-AI/Bilqis-MLX/commit/05ec82ec829b07a8553b923a2b48a617fa4756d1) `Merge pull request #563 from Entif-AI/codex/bamf02-b06-policy-20261029`
- [`856d12d61f0a`](https://github.com/Entif-AI/Bilqis-MLX/commit/856d12d61f0abbba7bf3b232343333ce055f725b) `Merge pull request #564 from Entif-AI/codex/bamf02-b07-transaction-20261029`
- [`ae08c4aa6c9e`](https://github.com/Entif-AI/Bilqis-MLX/commit/ae08c4aa6c9eee86cbc28142de626f382662876d) `Merge pull request #565 from Entif-AI/codex/bamf02-b09-adapters-20261029`
- [`cb22592c7bf0`](https://github.com/Entif-AI/Bilqis-MLX/commit/cb22592c7bf07494b865152cf7dd3f1255926bb9) `feat(bamf): prove B05 three-group boundary ordering`
- [`eef9ed83dba7`](https://github.com/Entif-AI/Bilqis-MLX/commit/eef9ed83dba729c7d1095537c1e33cea93c0f955) `docs(bamf): record B05.2 independent scoped EGM pass`
- [`8fba7685dfd4`](https://github.com/Entif-AI/Bilqis-MLX/commit/8fba7685dfd4c4265b11e6c0f7cd3962a3b08844) `fix(bamf): revalidate Atlas source and answer code before adoption`
- [`5f57d5291595`](https://github.com/Entif-AI/Bilqis-MLX/commit/5f57d529159576f58d2109910c1698215f7f8841) `docs(bamf): record C07 pre-adoption scoped EGM pass`
- [`b2b41e94aaa8`](https://github.com/Entif-AI/Bilqis-MLX/commit/b2b41e94aaa84c3b04fd86b7c80061405a93b974) `docs(bamf): reconcile A07 final EGM and parent evidence`
- [`f4e82c38bf68`](https://github.com/Entif-AI/Bilqis-MLX/commit/f4e82c38bf68f84c4cdeb872811c9639fefd54a9) `docs(bamf): time-qualify A07 pre-merge receipt`
- [`3bf1ef3e5031`](https://github.com/Entif-AI/Bilqis-MLX/commit/3bf1ef3e5031556b02d8e24fe9d43838cc14db12) `docs(bamf): record A07 evidence repair EGM clearance`
- [`629363bd27bb`](https://github.com/Entif-AI/Bilqis-MLX/commit/629363bd27bbef524467bf2b2aaa7f8170dfcba7) `docs: record A13 parent audit`
- [`31d830d3f04e`](https://github.com/Entif-AI/Bilqis-MLX/commit/31d830d3f04e651cc5165720e287d8df1d86a0dc) `test: exercise formal lesson variation axes`
- [`eec0e4323d15`](https://github.com/Entif-AI/Bilqis-MLX/commit/eec0e4323d1535173361d786fc4611135a8043ae) `docs: record A05 parent acceptance`
- [`dfc2915ef5c6`](https://github.com/Entif-AI/Bilqis-MLX/commit/dfc2915ef5c65de45e6c596caf2340971d3b5f73) `fix(bamf): break A02 factor authority cycle`
- [`be3b3ac434e3`](https://github.com/Entif-AI/Bilqis-MLX/commit/be3b3ac434e3fdaeed6dfcfdb710d82353cefc20) `docs(bamf): record A02 factor authority repair`
- [`40aa062f619c`](https://github.com/Entif-AI/Bilqis-MLX/commit/40aa062f619c8de870fae862794f3b6496a0ca21) `feat: source-bound morphology law proposals`
- [`8a3d5dcd2498`](https://github.com/Entif-AI/Bilqis-MLX/commit/8a3d5dcd24985de2857f08572b1ad968e57ea4e0) `docs: record A04 parent codec crosswalk`
- [`c23138ea0d32`](https://github.com/Entif-AI/Bilqis-MLX/commit/c23138ea0d32ebbcec6fcb693ebf18f53034e85b) `fix: bind Factory input to canonical A13 gate`
- [`a959dc4804c7`](https://github.com/Entif-AI/Bilqis-MLX/commit/a959dc4804c7c3abe35f47839d8bedc5a0b29708) `feat(bamf): stage source-bound A02 semantic bank allocation`
- [`8165a0a884ea`](https://github.com/Entif-AI/Bilqis-MLX/commit/8165a0a884eac00122ef6e1a5fef36add7a10cd9) `feat(bamf): stage complete A02 tensor tree and source mirror`
- [`c33b08d32e99`](https://github.com/Entif-AI/Bilqis-MLX/commit/c33b08d32e99f7a332ea8df3ddf28043809143ff) `test(bamf): pin source-hold feature and bank guards`
- [`6e492f70af09`](https://github.com/Entif-AI/Bilqis-MLX/commit/6e492f70af09f7c0bb387b79c9fa93d878800f85) `docs(bamf): record A02 admission integration handoff`
- [`af64e9c4844a`](https://github.com/Entif-AI/Bilqis-MLX/commit/af64e9c4844a8e9eab0425ffaa3ca42d30677512) `test(bamf): reject held real-source bank admission`
- [`333448aeec35`](https://github.com/Entif-AI/Bilqis-MLX/commit/333448aeec358bc192f200bdb11d001a87d3c01d) `feat(bamf): stage pinned A03 released schema body witnesses`
- [`ad14c7fc1bf1`](https://github.com/Entif-AI/Bilqis-MLX/commit/ad14c7fc1bf1af3258cc7c9795e7ab4694c1dc31) `feat(bamf): validate partial visible forests`
- [`c345a1d54909`](https://github.com/Entif-AI/Bilqis-MLX/commit/c345a1d54909c47a611e2df4840d13e7b406e0d4) `docs(bamf): record A05.4 candidate receipt`
- [`f797bf03b20f`](https://github.com/Entif-AI/Bilqis-MLX/commit/f797bf03b20f6962320ecf708c93b00c3684029f) `fix(bamf): reject forged A02 factor predecessors and slices`
- [`71db0929a3e7`](https://github.com/Entif-AI/Bilqis-MLX/commit/71db0929a3e7d6889f0aa86a7ef68e3616daee5b) `feat(bamf): pin actual A03 schema bodies to source release`
- [`f1c8b8b5793e`](https://github.com/Entif-AI/Bilqis-MLX/commit/f1c8b8b5793e384e540efd2fe0d669da45d8cb8f) `feat(bamf): validate partial visible forests`
- [`a2cd37cab98e`](https://github.com/Entif-AI/Bilqis-MLX/commit/a2cd37cab98e3199cca5bfd7eb5e61512480ee1d) `fix(bamf): derive A02 Registry descriptions from pinned SKOS definitions`
- [`97c69350a1b1`](https://github.com/Entif-AI/Bilqis-MLX/commit/97c69350a1b13de288dbf9a264b4f7159b8220b0) `test(bamf): reject foreign source bundle for Registry mirror`
- [`de2b4d3cf576`](https://github.com/Entif-AI/Bilqis-MLX/commit/de2b4d3cf576ebe9d5ae5d1bcaff2bcb1cd7b6f9) `docs(bamf): record A02 scoped independent EGM clearance`
- [`1297f3d6ecf0`](https://github.com/Entif-AI/Bilqis-MLX/commit/1297f3d6ecf0e445c062fbd18de012db1f4dfc44) `fix(bamf): verify source-pinned schema inside consumer gate`
- [`0d8571bc2b5e`](https://github.com/Entif-AI/Bilqis-MLX/commit/0d8571bc2b5ea8c7c8995161eccac9254abc2565) `feat(bamf): bind nested child closures without ABI identities`
- [`d19ccc7f1b98`](https://github.com/Entif-AI/Bilqis-MLX/commit/d19ccc7f1b989062bcf3fe54c95e322b4a7b7432) `fix(bamf): recheck hidden parent source authority`
- [`ee6c75bd470c`](https://github.com/Entif-AI/Bilqis-MLX/commit/ee6c75bd470c0046b742e8d74fde9150a3ddc4af) `docs(bamf): record A05.4 EGM repair`
- [`8f1b61ef9625`](https://github.com/Entif-AI/Bilqis-MLX/commit/8f1b61ef96257b740c0e2fcebaf9d3cdaed09f24) `fix(bamf): recheck hidden parent source authority`
- [`52b59940bdee`](https://github.com/Entif-AI/Bilqis-MLX/commit/52b59940bdee9d9fd287c47944f85d38f0d8dad0) `test(bamf): enforce hidden-parent grant revocation in B03`
- [`74be897cb978`](https://github.com/Entif-AI/Bilqis-MLX/commit/74be897cb978f3e08f501b8a832712ce97ff473a) `fix(bamf): bind child constituent to parent local slot`
- [`1bc68a0e8f62`](https://github.com/Entif-AI/Bilqis-MLX/commit/1bc68a0e8f62744c42848476119191bab38c992f) `fix(bamf): derive child slot bound from source tensor shape`
- [`49a426f0e7a8`](https://github.com/Entif-AI/Bilqis-MLX/commit/49a426f0e7a851158f77698fce677f50334552fb) `docs(bamf): record B02.4 independent EGM pass`
- [`369c87637430`](https://github.com/Entif-AI/Bilqis-MLX/commit/369c8763743072a508abc255bb793b75965d0cc0) `docs(bamf): record A03.4 independent EGM pass`
- [`5aacc45735dc`](https://github.com/Entif-AI/Bilqis-MLX/commit/5aacc45735dce012d84e0589a680fff5521005d7) `docs(bamf): record A05.4 EGM pass`
- [`19ebb053f4a1`](https://github.com/Entif-AI/Bilqis-MLX/commit/19ebb053f4a1115f073ded6f975de4a6cd6fe116) `feat(bamf): execute fixed unadmitted four-layer groups`
- [`baf52f167567`](https://github.com/Entif-AI/Bilqis-MLX/commit/baf52f167567c06ed5c2a9186da05d173fee1e03) `Merge remote-tracking branch 'origin/codex/bamf02-a03-4-schema-witness-20261029' into codex/bamf02-a-priority-integration-20261029`
- [`d733de2cea2c`](https://github.com/Entif-AI/Bilqis-MLX/commit/d733de2cea2cac1963382f203b9256df5add7d11) `Merge remote-tracking branch 'origin/codex/bamf02-a05-4-partial-forest-20261029' into codex/bamf02-a-priority-integration-20261029`
- [`9fb0d7956368`](https://github.com/Entif-AI/Bilqis-MLX/commit/9fb0d7956368ae7b8b7d53e9e1df804cd321cc7b) `docs(bamf): record A03.4 A05.4 combined source proof`
- [`bb936d81b9c0`](https://github.com/Entif-AI/Bilqis-MLX/commit/bb936d81b9c0fa47eb1f1ee00dd79777e3454ffb) `feat(bamf): fingerprint executed B04 group parameter and cache chains`
- [`7d74e5927f71`](https://github.com/Entif-AI/Bilqis-MLX/commit/7d74e5927f718367c0575b00bc93a7ea99abe328) `docs(bamf): record Lane A priority integration EGM pass`
- [`ef137c7b864d`](https://github.com/Entif-AI/Bilqis-MLX/commit/ef137c7b864de0fef9d525eae6a080996e9ad634) `docs(bamf): reconcile B02.4 source proof`
- [`a75e38dc07e2`](https://github.com/Entif-AI/Bilqis-MLX/commit/a75e38dc07e2db778c0516ac2c101e7ea2015f94) `feat(bamf): stage pinned A03 released schema body witnesses`
- [`89e25e1968cb`](https://github.com/Entif-AI/Bilqis-MLX/commit/89e25e1968cbea46e7b4b9c7a7524ae45b4a0e1a) `feat(bamf): pin actual A03 schema bodies to source release`
- [`23ffd5b9a65e`](https://github.com/Entif-AI/Bilqis-MLX/commit/23ffd5b9a65e15847b383f4786d07da97c6300fc) `fix(bamf): verify source-pinned schema inside consumer gate`
- [`e194e3c41879`](https://github.com/Entif-AI/Bilqis-MLX/commit/e194e3c418798ed6277560fc2b80bc0e8203864f) `docs(bamf): record A03.4 independent EGM pass`
- [`2e13848e5582`](https://github.com/Entif-AI/Bilqis-MLX/commit/2e13848e5582762fd23ae6c0a74f97acc57de91a) `feat(bamf): validate partial visible forests`
- [`a40448f7dbdc`](https://github.com/Entif-AI/Bilqis-MLX/commit/a40448f7dbdcae702e51df7ed8fe1b69114df325) `docs(bamf): record A05.4 candidate receipt`
- [`17b40858de20`](https://github.com/Entif-AI/Bilqis-MLX/commit/17b40858de20ae568ade31ada70d79590bec5e5f) `fix(bamf): recheck hidden parent source authority`
- [`660f24dffb0d`](https://github.com/Entif-AI/Bilqis-MLX/commit/660f24dffb0d34d81e379b91f1b097aaf0c0f426) `docs(bamf): record A05.4 EGM repair`
- [`49b7a612f033`](https://github.com/Entif-AI/Bilqis-MLX/commit/49b7a612f0336db7eaa308536fe78599c985195b) `docs(bamf): record A05.4 EGM pass`
- [`1b05518ca8fd`](https://github.com/Entif-AI/Bilqis-MLX/commit/1b05518ca8fd6819fd7ceed2e1dc52e0b5d48cb1) `docs(bamf): record A03.4 A05.4 combined source proof`
- [`56642918833b`](https://github.com/Entif-AI/Bilqis-MLX/commit/56642918833bea3957dd9b082cdeacdb8960ba86) `fix(bamf): break A02 factor authority cycle`
- [`1d9574e6eb17`](https://github.com/Entif-AI/Bilqis-MLX/commit/1d9574e6eb1730a5d964ed4cbf0dcdd160cebe14) `docs(bamf): record A02 factor authority repair`
- [`4cb128bbea8f`](https://github.com/Entif-AI/Bilqis-MLX/commit/4cb128bbea8fd06ad0774b206552de0896ddad58) `feat(bamf): stage source-bound A02 semantic bank allocation`
- [`ec2b3772db0f`](https://github.com/Entif-AI/Bilqis-MLX/commit/ec2b3772db0f79b49922dc3f1fab878e9dcabb62) `feat(bamf): stage complete A02 tensor tree and source mirror`
- [`654d9d6afb9b`](https://github.com/Entif-AI/Bilqis-MLX/commit/654d9d6afb9be578b9f6c123e8f610b9a4907a96) `test(bamf): pin source-hold feature and bank guards`
- [`5300fd00e983`](https://github.com/Entif-AI/Bilqis-MLX/commit/5300fd00e9831d28bf99c94820b88774b8fe0721) `docs(bamf): record A02 admission integration handoff`
- [`217f1fd9436a`](https://github.com/Entif-AI/Bilqis-MLX/commit/217f1fd9436a5499344c67f7e5c921cf4d142d60) `test(bamf): reject held real-source bank admission`
- [`2010d0b9dcad`](https://github.com/Entif-AI/Bilqis-MLX/commit/2010d0b9dcad4a272d23b83d4de1cf90dc19b6f5) `fix(bamf): reject forged A02 factor predecessors and slices`
- [`4bbf6b802c0f`](https://github.com/Entif-AI/Bilqis-MLX/commit/4bbf6b802c0fad5d7bc2b101d83fb184f9f3001c) `fix(bamf): derive A02 Registry descriptions from pinned SKOS definitions`
- [`a19891792f9a`](https://github.com/Entif-AI/Bilqis-MLX/commit/a19891792f9a5dd67c816652a7f9007387bfaf74) `test(bamf): reject foreign source bundle for Registry mirror`
- [`c64109a37636`](https://github.com/Entif-AI/Bilqis-MLX/commit/c64109a37636cbe1fa70939f6386ccd0a33100ff) `docs(bamf): record A02 scoped independent EGM clearance`
- [`d4be9810d4d9`](https://github.com/Entif-AI/Bilqis-MLX/commit/d4be9810d4d911941cddfc80d4588d6faf3e226a) `docs(bamf): record A03 A05 unified cut proof`
- [`bbd49ac188f2`](https://github.com/Entif-AI/Bilqis-MLX/commit/bbd49ac188f2a43a1d2a52a9b0d409bc45720186) `docs(bamf): record A02 unified staging proof`
- [`08b588c60574`](https://github.com/Entif-AI/Bilqis-MLX/commit/08b588c605743ab128099cf850a37fb66afde4c8) `fix(bamf): bind sequence resets and verify numerical predecessor chain`
- [`55a3fff21b7b`](https://github.com/Entif-AI/Bilqis-MLX/commit/55a3fff21b7b9b4e9e2e879be55e8ce05ce1396b) `feat(bamf): bridge compiled A05 frames to unadmitted B11 h0`
- [`53983a2a481d`](https://github.com/Entif-AI/Bilqis-MLX/commit/53983a2a481d015df18d249c1ddb9891ead56f82) `feat(bamf): derive source closure vectors from B01 and block atom custody`
- [`cce527964fde`](https://github.com/Entif-AI/Bilqis-MLX/commit/cce527964fde9164138d3e5bbdf7b908139a118c) `test(bamf): reject non-source-valid closure-only A05 prefix`
- [`c3fab66c5da2`](https://github.com/Entif-AI/Bilqis-MLX/commit/c3fab66c5da2d20704a7aeb6cd80def07337bce6) `ci(bamf): merge reviewed A03.4 + A05.4 source authority`
- [`da0431bee37c`](https://github.com/Entif-AI/Bilqis-MLX/commit/da0431bee37c0e4f766f05cc94ceb6b23ac7d054) `ci(bamf): merge reviewed A02 staging cut`
- [`ff2857c207d2`](https://github.com/Entif-AI/Bilqis-MLX/commit/ff2857c207d279526dc0f00c73682e296951fab9) `docs(bamf): specify source atom ABI authority seam`
- [`7907889358bd`](https://github.com/Entif-AI/Bilqis-MLX/commit/7907889358bdbb7a324be5f427ce85d03d07e76a) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/bamf02-b-neural`
- [`406c05012490`](https://github.com/Entif-AI/Bilqis-MLX/commit/406c05012490ed6eaa60c088238d624c3ba042c5) `docs(bamf): pin A05.5 atom authority and B08 no-hit gate`
- [`f832ad899b0f`](https://github.com/Entif-AI/Bilqis-MLX/commit/f832ad899b0f3f2c3b37aad1444ffff6ddf2e827) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/bamf02-c-runtime`
- [`813c5afd8961`](https://github.com/Entif-AI/Bilqis-MLX/commit/813c5afd8961ca41f7595f8cd93d246f5cfc0c0d) `docs(bamf): record reviewed unified refresh and bounded proofs`
- [`10e1b3e11091`](https://github.com/Entif-AI/Bilqis-MLX/commit/10e1b3e110915b15c9ca514450bff06256cb9eb8) `fix(bamf): own numerical backbone predecessor in execution session`
- [`9fb1f5df71ad`](https://github.com/Entif-AI/Bilqis-MLX/commit/9fb1f5df71ad852c9aeaeea8a0f6a991f3615a60) `feat(bamf): stage two source-gated motif read sites`
- [`eb6bcfcdb802`](https://github.com/Entif-AI/Bilqis-MLX/commit/eb6bcfcdb8026ee0b906263bc17140cdf732deda) `fix(bamf): quarantine unqualified motif reads pending source issuer`
- [`26c898c08308`](https://github.com/Entif-AI/Bilqis-MLX/commit/26c898c08308041190e15806fef9ba2e02508144) `feat(runtime): inspect native Atlas debt without changing authority`
- [`7080d6445404`](https://github.com/Entif-AI/Bilqis-MLX/commit/7080d6445404411c7d64ee26680d73cff06ce11f) `feat(bamf): stage native AdamW participation counts`
- [`1e7f525cec3f`](https://github.com/Entif-AI/Bilqis-MLX/commit/1e7f525cec3f8099a4740167fd0856f0897bd7a9) `fix(bamf): source-qualify quarantined group1 motif read`
- [`e487acb7ab4e`](https://github.com/Entif-AI/Bilqis-MLX/commit/e487acb7ab4ea351b3f2b73313921a19c27ac3d9) `Merge remote-tracking branch 'origin/codex/bamf02-b-neural' into codex/bamf02-b08-1-source-read-20261029`
- [`2f8e79ef7bcb`](https://github.com/Entif-AI/Bilqis-MLX/commit/2f8e79ef7bcb15b81488837189740ba371b28546) `fix(runtime): authenticate correction supersession and preserve temporal history`
- [`0a04c3c7a38f`](https://github.com/Entif-AI/Bilqis-MLX/commit/0a04c3c7a38f8d6a7cbae3c2f9635f2778c8edcd) `feat(bamf): stage persistent plasticity cadence policy`
- [`ef19f7ba8e9d`](https://github.com/Entif-AI/Bilqis-MLX/commit/ef19f7ba8e9da1054def2ab54282a2e711a76daf) `feat(runtime): renew disposable Atlas leases with predecessor fencing`
- [`2db706fe0fd1`](https://github.com/Entif-AI/Bilqis-MLX/commit/2db706fe0fd153eeb0801ffb4585b49d3204323b) `docs(bamf): record independent supersession re-audit`
- [`2cb561bb5f1b`](https://github.com/Entif-AI/Bilqis-MLX/commit/2cb561bb5f1be0e79e1baa4e821e935ba1e19c65) `feat(bamf): hold unowned source atom ABI mappings`
- [`1416d65231e5`](https://github.com/Entif-AI/Bilqis-MLX/commit/1416d65231e5f40d9db4d741dfe39487d2a6d543) `feat(bamf): mask participation before native gradient clipping`
- [`f22316bd69f4`](https://github.com/Entif-AI/Bilqis-MLX/commit/f22316bd69f4b05ad824c0e0ffef5a32d432a5e1) `fix(runtime): bind replay content and validate immutable worker packets`
- [`b9027026b1d6`](https://github.com/Entif-AI/Bilqis-MLX/commit/b9027026b1d624397ff233b33babc23147abb291) `docs(bamf): preserve exact red receipt without whitespace debt`
- [`a78ba2b8bf28`](https://github.com/Entif-AI/Bilqis-MLX/commit/a78ba2b8bf28a35200374c88f3ea61e3a64fbdc3) `feat(bamf): reuse B01 ledger for unbound optimizer state`
- [`0d5ca908badd`](https://github.com/Entif-AI/Bilqis-MLX/commit/0d5ca908badd71d54d067d6e386decda6ff6bf11) `fix(runtime): persist immutable outbox domain bindings`
- [`fb41e8649fa6`](https://github.com/Entif-AI/Bilqis-MLX/commit/fb41e8649fa6cce51197d4a594b796849876c955) `docs(bamf): checkpoint combined Lane C owner verification`
- [`d77ae1d31df4`](https://github.com/Entif-AI/Bilqis-MLX/commit/d77ae1d31df4c15bc86b1cd4633951d74fb784d8) `feat(runtime): project immutable generation outbox evidence`
- [`5fa0788727a2`](https://github.com/Entif-AI/Bilqis-MLX/commit/5fa0788727a2675526d762dfef11c1889d6f7fbb) `feat(runtime): receive opaque owner fixtures with explicit authority limits`
- [`250a7c9bb2b6`](https://github.com/Entif-AI/Bilqis-MLX/commit/250a7c9bb2b6b76e23bf990ad2c8980d2c099394) `fix(runtime): verify native Factory admission before generation projection`
- [`992d86faa958`](https://github.com/Entif-AI/Bilqis-MLX/commit/992d86faa95840809554b668b513dfa94e1c5d5a) `feat(runtime): consume native Rosetta Observation identity`
- [`53556fff9842`](https://github.com/Entif-AI/Bilqis-MLX/commit/53556fff98425e38a5e2dcd15fe2cc277a05a8c7) `refactor(scripts): compartmentalize tooling directory`
- [`ea6c365ce50b`](https://github.com/Entif-AI/Bilqis-MLX/commit/ea6c365ce50be0e3cabd5d35f2f750b71036471f) `refactor(bamf): split backlog grooming modules`
- [`044b22ce0b5c`](https://github.com/Entif-AI/Bilqis-MLX/commit/044b22ce0b5c77dc49e0d4037e983fcf879fcf69) `docs(governance): require anti-monolith interruption discipline`
- [`fcedf581a422`](https://github.com/Entif-AI/Bilqis-MLX/commit/fcedf581a422c0aa7a2ede0bc191014ae83919f4) `ci(bamf): consolidate semantic verification`
- [`db181db897f7`](https://github.com/Entif-AI/Bilqis-MLX/commit/db181db897f755f56a73bc80d312caddc8feab4d) `ci(governance): enforce anti-monolith development contract`
- [`f3c33e2ef066`](https://github.com/Entif-AI/Bilqis-MLX/commit/f3c33e2ef06650a04914d2660ca9cc5e14f0f08b) `feat(governance): enforce anti-monolith development discipline`
- [`234512a3b509`](https://github.com/Entif-AI/Bilqis-MLX/commit/234512a3b5096c65b90073880aac5c22e79140b6) `merge: sync unified governance into semantic CI cutover`
- [`3fe5b85d483b`](https://github.com/Entif-AI/Bilqis-MLX/commit/3fe5b85d483b6ade265fb32e6c7863f9f67514f0) `Merge PR #597: consolidate BAMF semantic verification`
- [`c1b0fe88af5f`](https://github.com/Entif-AI/Bilqis-MLX/commit/c1b0fe88af5f2c2a3af94668e522e9b38594cd81) `refactor(tests): compartmentalize script checks`
- [`11390de1a13d`](https://github.com/Entif-AI/Bilqis-MLX/commit/11390de1a13d48af930d4b7a0124d26c303c1c23) `fix(governance): scope enforcement from branch adoption`
- [`e93d06655b6b`](https://github.com/Entif-AI/Bilqis-MLX/commit/e93d06655b6b034b9fdda4a352904425e782b5cc) `Merge PR #599: scope anti-monolith checks from branch adoption`
- [`8c986221107b`](https://github.com/Entif-AI/Bilqis-MLX/commit/8c986221107b6061a153a44329cc8762e0b2646c) `refactor(semantics): split pure operator contracts and mirrored tests`
- [`e11670b6dcb7`](https://github.com/Entif-AI/Bilqis-MLX/commit/e11670b6dcb77155f0c38e632fa1ee790e23cc5a) `feat(bamf): evidence for BAMF A07 - reconcile final EGM and parent closure evidence`
- [`12e04350f76f`](https://github.com/Entif-AI/Bilqis-MLX/commit/12e04350f76f3d32c6e67957c667229d8906131b) `feat(bamf): work on BAMF A13 parent - preserve independent Factory-gate blocker`
- [`7d88957bf9dd`](https://github.com/Entif-AI/Bilqis-MLX/commit/7d88957bf9dd48eb0e6e18428c17d3080dc1df31) `feat(bamf): crosswalk - BAMF A05 parent acceptance`
- [`f5f0ecc418ac`](https://github.com/Entif-AI/Bilqis-MLX/commit/f5f0ecc418ac5f7e10266d9b94bd74fd68e4b723) `feat(bamf): normalized BAMF B05.2 - three-group boundary ordering and diagnostics, scoped`
- [`fe3690157502`](https://github.com/Entif-AI/Bilqis-MLX/commit/fe3690157502e1dbae31b6b08e7b85d6878d0ef4) `feat(bamf): revalidation, scoped - BAMF C07.1b - fail-closed source/answer before Atlas adoption`
- [`d32bde269d31`](https://github.com/Entif-AI/Bilqis-MLX/commit/d32bde269d313f03d11d7470c179a1611b4ce9ab) `refactor(bamf): split source-qualified cognitive operators and mirrored tests`
- [`d486b33a178c`](https://github.com/Entif-AI/Bilqis-MLX/commit/d486b33a178cf868374cfeb3a78ec15103525975) `feat(bamf): stage source-bound neural component contracts`
- [`4fdb3dc069e6`](https://github.com/Entif-AI/Bilqis-MLX/commit/4fdb3dc069e6c1f5a156cbf0c2551f2d8161e7f5) `feat(bamf): Lane C correction dependency and revalidation engine`
- [`bea0f2b4545e`](https://github.com/Entif-AI/Bilqis-MLX/commit/bea0f2b4545e83aa2b4c81930a93d81ded59fb0d) `feat(bamf): formal variation coverage for BAMF A08`
- [`5feac2356d49`](https://github.com/Entif-AI/Bilqis-MLX/commit/5feac2356d49f7b5c149ca0c639118130cdcdb3a) `feat(bamf): evidence bridge - BAMF A08 morphology source-law`
- [`89932f63572b`](https://github.com/Entif-AI/Bilqis-MLX/commit/89932f63572b5af3d8311164ce352d05df485816) `feat(bamf): stage source-bound A02 identity-bank allocation`
- [`9077f2e51d57`](https://github.com/Entif-AI/Bilqis-MLX/commit/9077f2e51d57e2f56a81b18b01f613cb0b56c2b5) `feat(bamf): bondage - BAMF B02.4 - bind nested child-frame constituents without invented identities`
- [`715ddc49e245`](https://github.com/Entif-AI/Bilqis-MLX/commit/715ddc49e245f09e4e7533e0024c88689e72913c) `feat(bamf): enforcer - BAMF C02.1 - canonical A13 eligibility before Factory input`
- [`60874e0444da`](https://github.com/Entif-AI/Bilqis-MLX/commit/60874e0444da18076de7dc01810b9193a7126784) `fix(governance): ignore unchanged base imports in branch scope`
- [`88935c060265`](https://github.com/Entif-AI/Bilqis-MLX/commit/88935c0602655f3ee59aff0dd32560bbf0864636) `refactor(factory): split source-family compiler and owner tests`
- [`cafbedfb1ba2`](https://github.com/Entif-AI/Bilqis-MLX/commit/cafbedfb1ba2070fa22a35a65bab37c4dbb7e631) `Merge PR #602: scope long-lived lanes to branch-authored changes`
- [`b001924b4352`](https://github.com/Entif-AI/Bilqis-MLX/commit/b001924b43526f2b6ab9c16dba2d82a8f8ba42a7) `feat(bamf): look both ways - BAMF A04 parent codec acceptance crosswalk`
- [`57a6388bc9a3`](https://github.com/Entif-AI/Bilqis-MLX/commit/57a6388bc9a38ac60cec812216a7b8b87710f625) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/bamf02-a08-skos-structure-cut-20261029`
- [`bbb7e74fed89`](https://github.com/Entif-AI/Bilqis-MLX/commit/bbb7e74fed894d96390cd976369d29011842617b) `feat(bamf): social distancing - B08.1 - source-qualify quarantined group1 motif read`
- [`66e907bc54be`](https://github.com/Entif-AI/Bilqis-MLX/commit/66e907bc54beba63ed4a8dea943076d0797f401d) `feat(bamf): abi or abi's sister - BAMF-0.2 A05.5 - fail closed on unowned raw atom ABI mappings`
- [`356935352623`](https://github.com/Entif-AI/Bilqis-MLX/commit/356935352623a2e7452d1828d91a3b826f2fae0d) `fix(governance): preserve requested base for branch scope`
- [`581dcd04fad8`](https://github.com/Entif-AI/Bilqis-MLX/commit/581dcd04fad8700554b8936cd20248975762d916) `Merge PR #604: preserve requested base for branch scope`
- [`95b8990f63b7`](https://github.com/Entif-AI/Bilqis-MLX/commit/95b8990f63b78aa430f64f47b23f8975ec816586) `fix(bamf): reconcile A09.1 source mirror and workstack hashes`
- [`4ebb3cbec0bf`](https://github.com/Entif-AI/Bilqis-MLX/commit/4ebb3cbec0bf4dcc9e397671d5d1e605534d0686) `fix(bamf): reconcile seven live owner mirrors and child hashes`
- [`44c198a0fea8`](https://github.com/Entif-AI/Bilqis-MLX/commit/44c198a0fea875594ade75b468d71b767a337a13) `Merge remote-tracking branch 'origin/codex/bamf02-c01-a09-mirror-20261029' into codex/bamf02-c01-owner-mirrors-20261029`
- [`74f493310ae3`](https://github.com/Entif-AI/Bilqis-MLX/commit/74f493310ae3f48f40004286058c89cec909ee5e) `docs(bamf): record combined live workstack validation`
- [`1a8dc9e81d78`](https://github.com/Entif-AI/Bilqis-MLX/commit/1a8dc9e81d78f533c619b9f18943ae7835e871de) `docs(bamf): record independent SKOS compiler structure EGM`
- [`76577e0c6452`](https://github.com/Entif-AI/Bilqis-MLX/commit/76577e0c645222523855fb317bea84775098e6b5) `docs(bamf): record independent C01 A09 mirror EGM`
- [`9be1f85cb9cc`](https://github.com/Entif-AI/Bilqis-MLX/commit/9be1f85cb9cc4ef5a53233af59696eb6e5c04721) `Merge remote-tracking branch 'origin/codex/bamf02-c01-a09-mirror-20261029' into codex/bamf02-c01-owner-mirrors-20261029`
- [`d0f0c73850ad`](https://github.com/Entif-AI/Bilqis-MLX/commit/d0f0c73850ad9b241fb8b21938a55a7557dbe638) `refactor(bamf): split A08 source-family compiler and source-corpus tests`
- [`8cbd615a3ea9`](https://github.com/Entif-AI/Bilqis-MLX/commit/8cbd615a3ea9fb0e0fc53a654b42c5a32e95bf12) `Merge pull request #605 from Entif-AI/codex/bamf02-c01-a09-mirror-20261029`
- [`ae5b72df9ad9`](https://github.com/Entif-AI/Bilqis-MLX/commit/ae5b72df9ad9c91637ffea9a9f9e823be50c5ec6) `fix(bamf): reconcile seven live owner mirrors and workstack ancestry`
- [`ab7a3cc3af1c`](https://github.com/Entif-AI/Bilqis-MLX/commit/ab7a3cc3af1c813f3427ffc01ab8f915cbaa6a76) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into HEAD`
- [`52fe01f80001`](https://github.com/Entif-AI/Bilqis-MLX/commit/52fe01f8000111c0af1112db91a68b0f2b221edb) `fix(bamf): make owner mirror reconciliation crash-resumable`
- [`9a67a2a5bba9`](https://github.com/Entif-AI/Bilqis-MLX/commit/9a67a2a5bba990c64c52ba24603cd9e2eb2b6aee) `feat(bamf): audit live recursive child registry completeness`
- [`3d000134c623`](https://github.com/Entif-AI/Bilqis-MLX/commit/3d000134c623d6c0386e028a6e71a3b92602bc49) `feat(bamf): audit missing and duplicate recursive child issues`
- [`0b90b52653ff`](https://github.com/Entif-AI/Bilqis-MLX/commit/0b90b52653ff7b38a2b42c550d7e4dcb3fbdaca4) `fix(bamf): make C01 owner mirror retries crash-resumable`
- [`d468b1af1c70`](https://github.com/Entif-AI/Bilqis-MLX/commit/d468b1af1c70a8dc0c0a7aa5ffa6d19b55cb2e18) `feat(bamf): cache - B11.1a #586 - executed group content/cache chain (unadmitted precursor)`
- [`387c87ecd6a9`](https://github.com/Entif-AI/Bilqis-MLX/commit/387c87ecd6a95baf54d0f121f49d1e0c11f3fa40) `refactor(bamf): reorganize A02 semantic vocabulary structure`
- [`57f8d9d878e5`](https://github.com/Entif-AI/Bilqis-MLX/commit/57f8d9d878e57429fdb7f4335167f5c6e7dcbdaa) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/bamf02-c-runtime`
- [`e024b9b405b7`](https://github.com/Entif-AI/Bilqis-MLX/commit/e024b9b405b7097bcefe962283c71a91a392dcd5) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/bamf02-a-sync-20261029`
- [`b78a500a8e0e`](https://github.com/Entif-AI/Bilqis-MLX/commit/b78a500a8e0e5393b6dabadbb112edd77332f1c2) `refactor(bamf): current-unified A02 semantic structure cleanup`
- [`03b214576524`](https://github.com/Entif-AI/Bilqis-MLX/commit/03b21457652421c8726314f3d3c7cb626b4d1677) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/bamf02-c-runtime`
- [`b3209343e2ba`](https://github.com/Entif-AI/Bilqis-MLX/commit/b3209343e2ba0f265e3be52fd68d5bc5b280c686) `refactor(factory): compartmentalize crowded roots`
- [`88f195a89fee`](https://github.com/Entif-AI/Bilqis-MLX/commit/88f195a89feeac75e97a041c212164514c445e76) `fix(factory): preserve skos test import compatibility`
- [`890582f41dd1`](https://github.com/Entif-AI/Bilqis-MLX/commit/890582f41dd1e8dd76223b4db0bcbec761067bb0) `test(factory): split real corpus adversaries`
- [`8b108956eaa7`](https://github.com/Entif-AI/Bilqis-MLX/commit/8b108956eaa76ba2fc738014a3a4186a426dfa03) `feat(bamf): source-bind formal operators without granting execution`
- [`cf75f9250212`](https://github.com/Entif-AI/Bilqis-MLX/commit/cf75f925021258365402ed11a1e3335711ebab70) `fix(bamf): distinguish formal source projections from attestation`
- [`ab6b825f1f7c`](https://github.com/Entif-AI/Bilqis-MLX/commit/ab6b825f1f7c48f4fd84bd9d6491f62181ff33d3) `fix(bamf): require source replay for formal operator proposals`
- [`3c05e817b758`](https://github.com/Entif-AI/Bilqis-MLX/commit/3c05e817b75846011f36843155d6c29b1b8ef477) `fix(bamf): reject formal source proposal equality spoofing`
- [`0a751c0895c5`](https://github.com/Entif-AI/Bilqis-MLX/commit/0a751c0895c574c1ee426cbb44e5165bb37b56af) `feat(bamf): task-scoped formal lessons with A13 rights replay`
- [`bd415666a0ec`](https://github.com/Entif-AI/Bilqis-MLX/commit/bd415666a0ec6d748858b02010ad270a9d7c202c) `fix(bamf): reject mutated formal typed values`
- [`3f3a1fbad01a`](https://github.com/Entif-AI/Bilqis-MLX/commit/3f3a1fbad01af622c531b1a462691ed24c3be23a) `fix(bamf): revalidate formal lesson authority on check`
- [`bafbdb58a8cc`](https://github.com/Entif-AI/Bilqis-MLX/commit/bafbdb58a8cc31e58e063cfb0faf7cf09a9efe16) `docs: record scoped formal lesson EGM clearance`
- [`e29b0025bbbb`](https://github.com/Entif-AI/Bilqis-MLX/commit/e29b0025bbbb893d69dce2f4c820b7a113004702) `Merge pull request #615 from Entif-AI/refactor/bamf-factory-roots-20261030`
- [`74c5e2ac142a`](https://github.com/Entif-AI/Bilqis-MLX/commit/74c5e2ac142a60142a9cc85fa92a4c502f458780) `refactor(bamf): fit A08 formal lessons to Factory compartments`
- [`590f6297cb9b`](https://github.com/Entif-AI/Bilqis-MLX/commit/590f6297cb9b5457d65e44e239c9e84a80140f02) `Merge pull request #616 from Entif-AI/feature/bamf-a08-1b2-recut-20261030`
- [`0a563eb67397`](https://github.com/Entif-AI/Bilqis-MLX/commit/0a563eb673972f5b17db567e3cc1c887e657343f) `ci: install semantic deps before integrity check`
- [`fe00fb35025e`](https://github.com/Entif-AI/Bilqis-MLX/commit/fe00fb35025eaf5147798ce5d275277f8f7bbf87) `ci: classify BAMF pull requests by base branch`
- [`4c8de5181f96`](https://github.com/Entif-AI/Bilqis-MLX/commit/4c8de5181f96583a01959e05500e00196c29db54) `ci: follow compartmentalized Factory test paths`
- [`951041ce1995`](https://github.com/Entif-AI/Bilqis-MLX/commit/951041ce1995ca2e8cd4ed56abc89ed8a5426d49) `Merge pull request #617 from Entif-AI/fix/ci-semantic-deps-before-integrity-20261030`
- [`7356a66b7788`](https://github.com/Entif-AI/Bilqis-MLX/commit/7356a66b77881a3dbedf3bd8c6251fcfc95be7f3) `refactor(semantics): split A05.5 atom binding contracts and tests`
- [`c667b7079e27`](https://github.com/Entif-AI/Bilqis-MLX/commit/c667b7079e2708926dedba5191305553b13ca31b) `refactor(semantics): separate source frame adapters by dialect`
- [`d58b2b403933`](https://github.com/Entif-AI/Bilqis-MLX/commit/d58b2b403933d9e58e4c8056369d7d677e24b057) `feat(semantics): bind reproduced source atoms to pinned A01 authority`
- [`0959aec34a08`](https://github.com/Entif-AI/Bilqis-MLX/commit/0959aec34a082bac2c2948e236dee9bc2e21ed87) `refactor(tests): isolate Atlas and context verification cases`
- [`7031a1bbf67f`](https://github.com/Entif-AI/Bilqis-MLX/commit/7031a1bbf67f7511dc0d46f8ac7179e64cd4af9c) `refactor(semantics): isolate source checks and immutable adapter lookup`
- [`6dabcff67708`](https://github.com/Entif-AI/Bilqis-MLX/commit/6dabcff677081ccc153e85d6f10fc76d30f53e31) `feat(learning): derive source-bound B03 vectors from canonical B01 state`
- [`763ec4e22a60`](https://github.com/Entif-AI/Bilqis-MLX/commit/763ec4e22a60bd28777ad81b28194befb3897ce3) `docs(bamf): restore A05.5 checked-in source contract`
- [`f0b44aa6f597`](https://github.com/Entif-AI/Bilqis-MLX/commit/f0b44aa6f597b13de5066d9af5a8dd75cf4ebeff) `style(tests): normalize frame adapter helper EOF`
- [`eac29b8be9e4`](https://github.com/Entif-AI/Bilqis-MLX/commit/eac29b8be9e4e92470422570ce4fc0a96837f05e) `ci: follow compartmentalized Learning test paths`
- [`a02b9ed45ead`](https://github.com/Entif-AI/Bilqis-MLX/commit/a02b9ed45ead1801be6dff655866b73be0ffc8ff) `Merge pull request #618 from Entif-AI/feature/bamf-a05-5-recut-20261030`
- [`a017004e5d29`](https://github.com/Entif-AI/Bilqis-MLX/commit/a017004e5d291c51973bff46d32b4145e9ac2959) `feat(bamf): source-attested scope and modality contrast candidates (#556)`
- [`ea595e9dc78c`](https://github.com/Entif-AI/Bilqis-MLX/commit/ea595e9dc78c8717fea510df3b2ca73dc59fd681) `feat(bamf): retain held scope and transformation source debt (#556)`
- [`840e6ce0664c`](https://github.com/Entif-AI/Bilqis-MLX/commit/840e6ce0664c98ffb6d190ca9581b99d3e19ab9b) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/bamf02-c-runtime`
- [`db24cfa05542`](https://github.com/Entif-AI/Bilqis-MLX/commit/db24cfa05542f51579606d6f3bfaabe21982643f) `refactor(runtime): preserve C10 owner imports in cohesive groups`
- [`e80e983b9345`](https://github.com/Entif-AI/Bilqis-MLX/commit/e80e983b93452276760d53a93ee2e67796e6c41d) `refactor(tests): mirror runtime ownership and prove stable imports`
- [`557663d0186e`](https://github.com/Entif-AI/Bilqis-MLX/commit/557663d0186ebb45e7381872fae60b47d68e1941) `refactor(runtime): split C10 staging contracts queries and storage`
- [`a0891dec3a7c`](https://github.com/Entif-AI/Bilqis-MLX/commit/a0891dec3a7c41d2122a5eca46212acfcef256e2) `fix(runtime): revalidate staging proofs and cold-read identities`
- [`ff96a5e08a0d`](https://github.com/Entif-AI/Bilqis-MLX/commit/ff96a5e08a0d171f5be7c8e95f071f22065bb220) `fix(runtime): reject malformed staging records before public access`
- [`1edc4ec0ec35`](https://github.com/Entif-AI/Bilqis-MLX/commit/1edc4ec0ec359232746c4e2dcfdffa6e48a73522) `feat(readout): bind native values and released role outputs`
- [`61c35e262efc`](https://github.com/Entif-AI/Bilqis-MLX/commit/61c35e262efcd3acbc0e3885422a5faeaeb85a18) `docs(readout): record B10.1 independent review and proof`
- [`f248d020ae04`](https://github.com/Entif-AI/Bilqis-MLX/commit/f248d020ae04bf359f51e5abc0c4d175cdceec03) `refactor(runtime): separate Atlas lease contracts and storage`
- [`de5467f7441f`](https://github.com/Entif-AI/Bilqis-MLX/commit/de5467f7441f682873ba35f64510cf868334c3ea) `refactor(runtime): reuse Lane C batch adapter compartments`
- [`569bc4353192`](https://github.com/Entif-AI/Bilqis-MLX/commit/569bc43531921c6c1ac6178d5ed953b006039800) `docs(readout): distinguish inherited error-control gate failure`
- [`113d43a23cc2`](https://github.com/Entif-AI/Bilqis-MLX/commit/113d43a23cc27d2101d5c9555f49f672f4e75336) `refactor(runtime): reuse Lane C correction owner compartments`
- [`9710f1ea8d78`](https://github.com/Entif-AI/Bilqis-MLX/commit/9710f1ea8d7847c4f896220fee5dc33ddaa4ffae) `refactor(runtime): reuse temporal projection and stale replay owners`
- [`b591cf2cc73b`](https://github.com/Entif-AI/Bilqis-MLX/commit/b591cf2cc73bac5f6a4b3c373d2c367e095f6408) `refactor(runtime): reuse candidate evidence and mirrored learning proofs`
- [`278b67d9b1b4`](https://github.com/Entif-AI/Bilqis-MLX/commit/278b67d9b1b4b3dd99d8636f2a3b40f5a32cdd85) `refactor(runtime): separate complete solver evaluation from retention decisions`
- [`8dfef6f387f0`](https://github.com/Entif-AI/Bilqis-MLX/commit/8dfef6f387f00126bada7bc9c6fe5dd332bccdbe) `refactor(runtime): compartmentalize original C10 outbox without batch changes`
- [`a131aea8e6b5`](https://github.com/Entif-AI/Bilqis-MLX/commit/a131aea8e6b5a0d57e3aedf5bd4e362fb8d2f2d5) `refactor(runtime): separate source repair and resume metadata reconciliation`
- [`9b629388fabc`](https://github.com/Entif-AI/Bilqis-MLX/commit/9b629388fabc67e7f9f3e4494f564044fafb502a) `refactor(runtime): separate depth contracts and mirrored MLX proofs`
- [`5b7e67933cfb`](https://github.com/Entif-AI/Bilqis-MLX/commit/5b7e67933cfb5ae926d2092dbc190442b0efc724) `refactor(tests): split solver routing replay and import-boundary proofs`
- [`cabd7a7b8737`](https://github.com/Entif-AI/Bilqis-MLX/commit/cabd7a7b87372467015386d96bfa40028fec0baf) `refactor(tests): separate causal convolution and native GQA witnesses`
- [`776ba2569341`](https://github.com/Entif-AI/Bilqis-MLX/commit/776ba2569341ae01bd78a6c5a26161c59f5a8886) `refactor(tests): group resource planning retry and worker proofs`
- [`da693249f549`](https://github.com/Entif-AI/Bilqis-MLX/commit/da693249f549e16af54d8cf3e6a6ceb0736414cc) `refactor(tests): group topology contracts ledgers storage and compatibility`
- [`6d4c400d125c`](https://github.com/Entif-AI/Bilqis-MLX/commit/6d4c400d125c8d91bb00c76bd7e540caa2b9b6d7) `refactor(runtime): freeze projection contracts and name resume error identity`
- [`93e67ed2f6de`](https://github.com/Entif-AI/Bilqis-MLX/commit/93e67ed2f6de48d9f7fe6fdfc812d5c395063f67) `refactor(runtime): separate temporal validation and correction test fixtures`
- [`e7d188d56c50`](https://github.com/Entif-AI/Bilqis-MLX/commit/e7d188d56c50b524447cc1d5b9553ec3b50f89ed) `refactor(runtime): extract unadmitted backbone group input validation`
- [`bd466a9851d3`](https://github.com/Entif-AI/Bilqis-MLX/commit/bd466a9851d3554632724a69035d048ee1003554) `refactor(runtime): separate refinement source contracts ranking and selection`
- [`6a3c714f4ede`](https://github.com/Entif-AI/Bilqis-MLX/commit/6a3c714f4ededfb4220b68c4145621fd039a8d7d) `docs(bamf): record C10.3 structure and named M3 proof boundaries`
- [`a1f6c852e3ef`](https://github.com/Entif-AI/Bilqis-MLX/commit/a1f6c852e3ef4dd6736ef0bb676dcba38c404cc1) `ci(bamf): follow grouped runtime test ownership`
- [`99f30680a498`](https://github.com/Entif-AI/Bilqis-MLX/commit/99f30680a498c51bd434626241e5fd27e9f54b26) `test(runtime): follow current docs and qualification helper owners`
- [`2394c610150d`](https://github.com/Entif-AI/Bilqis-MLX/commit/2394c610150d2ad72621683b23c01723aee4e98d) `docs(bamf): checkpoint C10.3 exact-source verification and scoped review`
- [`e075c8752212`](https://github.com/Entif-AI/Bilqis-MLX/commit/e075c8752212294cdef35a8974ec8c86a535b641) `Merge commit '569bc43531921c6c1ac6178d5ed953b006039800' into codex/bamf02-b10-2-468-20261030`
- [`6f61d3c49bdc`](https://github.com/Entif-AI/Bilqis-MLX/commit/6f61d3c49bdc79181bde9ba678c7d22ac49b853f) `feat(readout): add bounded control and structured frame commits`
- [`003a9a52f335`](https://github.com/Entif-AI/Bilqis-MLX/commit/003a9a52f335e01cc73e3ecd80c311fa95d811f4) `docs(readout): specify B10.2 record and source boundaries`
- [`c710902726a2`](https://github.com/Entif-AI/Bilqis-MLX/commit/c710902726a2540e3389c51c3c3506a13cef6b34) `test(readout): verify B10.2 publication barrier and record proof`
- [`e1ada677c1f0`](https://github.com/Entif-AI/Bilqis-MLX/commit/e1ada677c1f05250d1d5c11b76607d397f5b8c68) `test(bamf): preserve held scope authority boundary (#556)`
- [`11c2bda93ec1`](https://github.com/Entif-AI/Bilqis-MLX/commit/11c2bda93ec18b2437ecf62fa03b9befdbc09862) `docs(bamf): refresh A08.1b.4 re-cut proof (#556)`
- [`8a7b00be062b`](https://github.com/Entif-AI/Bilqis-MLX/commit/8a7b00be062b5706196d8506f02129de5f24598e) `feat(readout): bind native values and released role outputs (B10.1)`
- [`cef08e8a3e58`](https://github.com/Entif-AI/Bilqis-MLX/commit/cef08e8a3e581d2f8775704567695c12bce7e336) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into feature/bamf-a08-1b4-complete-20261030`
- [`d70acc2e4cae`](https://github.com/Entif-AI/Bilqis-MLX/commit/d70acc2e4cae333e2c1c32b24c7d5500a9d53d30) `docs(bamf): record latest unified sync for A08.1b.4 (#556)`
- [`dde9398249cb`](https://github.com/Entif-AI/Bilqis-MLX/commit/dde9398249cb1dc23c9c979f0e7162436aaae894) `feat(readout): bounded CONTROL decisions and validated frame output (B10.2)`
- [`8e210ea41ea7`](https://github.com/Entif-AI/Bilqis-MLX/commit/8e210ea41ea7c508c683fa341af27a993fc2d70a) `docs(bamf): record A08.1b.4 EGM pass (#556)`
- [`aac11b05750c`](https://github.com/Entif-AI/Bilqis-MLX/commit/aac11b05750c07bb5d7694cac74a08074c930784) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into feature/bamf-a08-1b4-complete-20261030`
- [`752c4b48b16b`](https://github.com/Entif-AI/Bilqis-MLX/commit/752c4b48b16b5b10adc9d3d508e752c6c70c35ac) `docs(bamf): record final A08.1b.4 unified sync (#556)`
- [`2f6cc6107993`](https://github.com/Entif-AI/Bilqis-MLX/commit/2f6cc6107993311389efa6e66832cb9207775e9a) `Merge pull request #624 from Entif-AI/feature/bamf-a08-1b4-complete-20261030`
- [`23522772d5cd`](https://github.com/Entif-AI/Bilqis-MLX/commit/23522772d5cd56c31191200619560e8af2a27b2a) `test(bamf): complete A08.1b.2 formal variation gate (#554)`
- [`afd6d24acd85`](https://github.com/Entif-AI/Bilqis-MLX/commit/afd6d24acd852c240d6b79dbe7dfc2a15c7c4242) `fix(bamf): make formal variation contract immutable (#554)`
- [`43ae1638bc46`](https://github.com/Entif-AI/Bilqis-MLX/commit/43ae1638bc46b0314bae9511ea749d7e80582cf4) `feat(bamf): re-cut source-bound morphology lessons (#555)`
- [`5071ff8995c4`](https://github.com/Entif-AI/Bilqis-MLX/commit/5071ff8995c4ae307876eb954dd6a32a34b890aa) `test(bamf): repair real-corpus paths after Factory split (#554)`
- [`537c6e8987be`](https://github.com/Entif-AI/Bilqis-MLX/commit/537c6e8987bed16af4fefe85c10ba94b0406b75a) `fix(bamf): reject mismatched A01 COUNT authority (#554)`
- [`267fc4777c17`](https://github.com/Entif-AI/Bilqis-MLX/commit/267fc4777c1777fe1bc524d942116e351086397c) `docs(bamf): record A08.1b.2 final EGM acceptance (#554)`
- [`7ce17dfd93c3`](https://github.com/Entif-AI/Bilqis-MLX/commit/7ce17dfd93c37ff643d0b18ccc10803ac417d352) `Merge pull request #626 from Entif-AI/feature/bamf-a08-1b2-acceptance-20261030`
- [`225a5adcfb90`](https://github.com/Entif-AI/Bilqis-MLX/commit/225a5adcfb909630ce47c6961fbbc1933cc098a8) `fix(bamf): consume canonical morphology source owner (#555)`
- [`e54ac725441c`](https://github.com/Entif-AI/Bilqis-MLX/commit/e54ac725441c91acee71fcf916fe09738e33db5b) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into feature/bamf-a08-1b3-recut-20261030`
- [`434a99ee7e20`](https://github.com/Entif-AI/Bilqis-MLX/commit/434a99ee7e20dfa2eb165c1230a47cdb4b762bb8) `refactor(skos): isolate composition source witness (#555)`
- [`9af11fd77053`](https://github.com/Entif-AI/Bilqis-MLX/commit/9af11fd770535e089115da5510373396df227a42) `fix(bamf): reject held morphology prerequisites (#555)`
- [`0af9826c2171`](https://github.com/Entif-AI/Bilqis-MLX/commit/0af9826c2171fdef8477fb991e10cc2d45ed50a7) `docs(bamf): record A08.1b.3 final EGM acceptance (#555)`
- [`9104ce733e04`](https://github.com/Entif-AI/Bilqis-MLX/commit/9104ce733e04fb9c82420428b18dfdbf5db49535) `Merge pull request #627 from Entif-AI/feature/bamf-a08-1b3-recut-20261030`
- [`c18419b50021`](https://github.com/Entif-AI/Bilqis-MLX/commit/c18419b500216fb7e25a460ecc45aa1b522f3fb4) `merge(bamf): sync Lane A with unified 2026-10-30`
- [`89398df8686a`](https://github.com/Entif-AI/Bilqis-MLX/commit/89398df8686a288d2ce77e65e68b847228ba9af2) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/bamf02-c-runtime`
- [`9bb14b40729d`](https://github.com/Entif-AI/Bilqis-MLX/commit/9bb14b40729d2ebfa4e73ff5c09ff0642c4c64c4) `refactor(bamf): split frame encoder ownership for B03.3`
- [`2a59fe091ff4`](https://github.com/Entif-AI/Bilqis-MLX/commit/2a59fe091ff4ebe5d3d181b3cdbf7358b1c66154) `fix(ci): make BAMF PR debt gate base-aware`
- [`1befa0fdc6af`](https://github.com/Entif-AI/Bilqis-MLX/commit/1befa0fdc6afdc0f3d4266ac00008498c272c69b) `fix(ci): follow relocated portable owners`
- [`7ad2624d78ce`](https://github.com/Entif-AI/Bilqis-MLX/commit/7ad2624d78ce62eb36887f88b6618fbc6d7978cf) `test(bamf): qualify nested frame lineage and compiler counts`
- [`2125c4016795`](https://github.com/Entif-AI/Bilqis-MLX/commit/2125c4016795ea2d6d64701beba7a0a24d38c6a0) `refactor(bamf): split quarantined motif read ownership`
- [`43eaeb332a6d`](https://github.com/Entif-AI/Bilqis-MLX/commit/43eaeb332a6db6f06469ba38b2608b778c7c5f93) `refactor(cli): separate operator owners and repair encountered directories`
- [`3ca7737d7300`](https://github.com/Entif-AI/Bilqis-MLX/commit/3ca7737d7300052006c98e919f52974969ab8953) `refactor(bamf): separate motif validation and source witnesses`
- [`5cf0fcdcc057`](https://github.com/Entif-AI/Bilqis-MLX/commit/5cf0fcdcc0573ebf940e599be24268dd2ea7171d) `refactor(bamf): isolate motif validation lookup and gate equations`
- [`e9ca8057d0a8`](https://github.com/Entif-AI/Bilqis-MLX/commit/e9ca8057d0a853d0e78b07946008cda4e4ebd181) `docs(bamf): record final motif structure review`
- [`7b0bad51f4c7`](https://github.com/Entif-AI/Bilqis-MLX/commit/7b0bad51f4c7d7cd0c43c9bdd619ba3ce765aa86) `refactor(tests): split numeric staircase enrollment and custody proofs`
- [`a4c17feaf341`](https://github.com/Entif-AI/Bilqis-MLX/commit/a4c17feaf3417f1b0a875cbbe61fb10f4763172f) `refactor(verification): split generated test contracts and publication`
- [`2d484899089d`](https://github.com/Entif-AI/Bilqis-MLX/commit/2d484899089dcfc323a3dd085fada1c05a65a061) `feat(bamf): derive stable capability identity from semantics`
- [`e376e8db8392`](https://github.com/Entif-AI/Bilqis-MLX/commit/e376e8db8392b04fbc54e615fa8d0532ef954ea0) `refactor(atlas): split source feature and prospective planning owners`
- [`1b1023383752`](https://github.com/Entif-AI/Bilqis-MLX/commit/1b1023383752545cb85fa1f3b2a1a68b7ddfe050) `refactor(scripts): group Rosetta bridge and record open integration gates`
- [`e82ad80156e0`](https://github.com/Entif-AI/Bilqis-MLX/commit/e82ad80156e039d2368ed089f81c8db22e9f8975) `feat(bamf): derive motif gate inputs from source-bound categorical factors`
- [`833c02291d44`](https://github.com/Entif-AI/Bilqis-MLX/commit/833c02291d449c612e5be9b3b0c4cbe73cd8a88c) `feat(bamf): start unadmitted backbone execution from replayed source atoms`
- [`537a8ed10277`](https://github.com/Entif-AI/Bilqis-MLX/commit/537a8ed102774492c1cda61bc8879a93214a9bf4) `feat(bamf): enforce causal typed-decoder feedback`
- [`7f074d00097b`](https://github.com/Entif-AI/Bilqis-MLX/commit/7f074d00097ba8147ebf02261e5b49592eda9d1b) `fix(bamf): validate forced decoder feedback`
- [`b0fa18ec08f2`](https://github.com/Entif-AI/Bilqis-MLX/commit/b0fa18ec08f202b4e343b8e1b849b16df9847c21) `feat(bamf): bind readout census to B01 ledger`
- [`cac728ef55cb`](https://github.com/Entif-AI/Bilqis-MLX/commit/cac728ef55cbd1086c29eab74dfb8ae6ccf2331b) `fix(ci): distinguish adapter factors from grade dispatch`
- [`25aefe08cad6`](https://github.com/Entif-AI/Bilqis-MLX/commit/25aefe08cad687971256f21ade6bf3a2673282fd) `fix(bamf): enforce dynamic teacher target legality`
- [`4fadd217d1d4`](https://github.com/Entif-AI/Bilqis-MLX/commit/4fadd217d1d4234e36df38c92462639e3440750f) `fix(ci): keep portable repair outside runtime debt`
- [`b2c9301b7caa`](https://github.com/Entif-AI/Bilqis-MLX/commit/b2c9301b7caa555948e711da216cd75bce4e7db5) `fix(ci): freeze logical source compartment mapping`
- [`6218f8b8adde`](https://github.com/Entif-AI/Bilqis-MLX/commit/6218f8b8adde8d29dff10e15e40aa87ac63c224e) `docs(bamf): close B10.3 review receipts`
- [`035607123645`](https://github.com/Entif-AI/Bilqis-MLX/commit/035607123645fc113f9040c3cda1ce339e3aa4e9) `docs(bamf): align B10.4 turn-in contract`
- [`2d94775e11a3`](https://github.com/Entif-AI/Bilqis-MLX/commit/2d94775e11a35cb38f94c938e703081721295ab0) `fix(ci): restore portable moved-owner compatibility`
- [`c8b2734bb405`](https://github.com/Entif-AI/Bilqis-MLX/commit/c8b2734bb405ed8177bbaa497c857035bbdc5dfa) `fix(bamf): enforce typed B10.3 value legality`
- [`ee3ca0a70191`](https://github.com/Entif-AI/Bilqis-MLX/commit/ee3ca0a701917b26da8a449d8ced25dd966daf9b) `docs(bamf): close B10.3 re-audit scope`
- [`f63aef10e598`](https://github.com/Entif-AI/Bilqis-MLX/commit/f63aef10e5988b4c5189b0e82c244b95f312fd9e) `chore(bamf): compose exact same-lane readout prerequisites`
- [`1bf6dbd3f537`](https://github.com/Entif-AI/Bilqis-MLX/commit/1bf6dbd3f53765b19a862876479331ce8b5e4c8b) `refactor(semantics): split atlas projection owners preserving artifacts`
- [`7d00bcd70de7`](https://github.com/Entif-AI/Bilqis-MLX/commit/7d00bcd70de7e16383fdd4030a97f832923ab7e8) `refactor(semantics): isolate source validation and freeze shape policy`
- [`5ca3b331ad6b`](https://github.com/Entif-AI/Bilqis-MLX/commit/5ca3b331ad6bb8d33cf5ce6ce27b19df6a88987b) `feat(bamf): preserve bounded decoder composition candidate`
- [`ab54b9d00836`](https://github.com/Entif-AI/Bilqis-MLX/commit/ab54b9d00836fffe4250574f437ef41ff9ae5850) `fix(bamf): preserve B10.3 boundary failures`
- [`e09197944837`](https://github.com/Entif-AI/Bilqis-MLX/commit/e091979448371718aae8dfcc6d17374aa964d771) `feat(bamf): reuse causal and parameter owners in typed prediction`
- [`3b6edd15c6e7`](https://github.com/Entif-AI/Bilqis-MLX/commit/3b6edd15c6e729d51c6c9d392087eecfe8937be5) `Merge remote-tracking branch 'origin/feature/bamf-b10-3-469-20261030' into codex/bamf02-b10-5-635-20261030`
- [`447cfc3632ae`](https://github.com/Entif-AI/Bilqis-MLX/commit/447cfc3632aeedb0c6a4a21b792b980c842ec8d2) `test(bamf): prove causal readout composition and record scoped acceptance`
- [`3d394da7a5b2`](https://github.com/Entif-AI/Bilqis-MLX/commit/3d394da7a5b23accc357a5ee941930630d016e6b) `fix(bamf): close B10.3 typed causal edge cases`
- [`b9ebf447b870`](https://github.com/Entif-AI/Bilqis-MLX/commit/b9ebf447b870471c62d0be188ef641fd0ee7c2b5) `fix(bamf): replay teacher causal ancestors only`
- [`828df66d1779`](https://github.com/Entif-AI/Bilqis-MLX/commit/828df66d17796c9147095da6f03fd1767f770a40) `fix(bamf): rebuild A09.1a clean turn-in`
- [`9e9fb9f1c3fe`](https://github.com/Entif-AI/Bilqis-MLX/commit/9e9fb9f1c3fe7a28a54474ce561d3b8c22310cc4) `docs(bamf): refresh B10.4 prerequisite receipt`
- [`014b0b80901f`](https://github.com/Entif-AI/Bilqis-MLX/commit/014b0b80901fe0cb11f250cf6d0f00742f1a4b55) `docs(bamf): refresh B10.5 prerequisite heads`
- [`f8117e9d3e57`](https://github.com/Entif-AI/Bilqis-MLX/commit/f8117e9d3e57f925a48100ca2b6204887204d31e) `docs(bamf): preserve source backbone proof and structural hold`
- [`b0f22b196b62`](https://github.com/Entif-AI/Bilqis-MLX/commit/b0f22b196b62354f1196240687f77e145090c6ec) `refactor(verification): split semantic coverage owners and mirrored tests`
- [`2cc49bd90d0b`](https://github.com/Entif-AI/Bilqis-MLX/commit/2cc49bd90d0b6767c4621b48ca57bcb73082c735) `refactor(pedagogy): split predecessor owners and protect source pins`
- [`500b6d2f471e`](https://github.com/Entif-AI/Bilqis-MLX/commit/500b6d2f471ea7bc85f14f0181b4eecdb0298c40) `docs(bamf): checkpoint coverage and predecessor structure proof`
- [`f63b88e3d3cf`](https://github.com/Entif-AI/Bilqis-MLX/commit/f63b88e3d3cfe8c7d98597a5305c5f145ea53ebd) `fix(quality): distinguish relocated operator debt from growth`
- [`6741be880222`](https://github.com/Entif-AI/Bilqis-MLX/commit/6741be88022252dd8a0b10f41922fe745e2ebd88) `refactor(bamf): mirror motif allocation test owners (#475)`
- [`826a16619fd4`](https://github.com/Entif-AI/Bilqis-MLX/commit/826a16619fd44fe95d7ed9d52f1be23036ad5e79) `refactor(presentation): split School50 telemetry ownership`
- [`02290261fba4`](https://github.com/Entif-AI/Bilqis-MLX/commit/02290261fba48d9eeeede1ce4c264d24e6fe1fab) `feat(bamf): stage in-memory candidate custody (#475)`
- [`6a75a124b51a`](https://github.com/Entif-AI/Bilqis-MLX/commit/6a75a124b51a9886be2e9e3eb14335b7b2fed5be) `refactor(presentation): split bounded terminal renderer owners`
- [`6aba55be82de`](https://github.com/Entif-AI/Bilqis-MLX/commit/6aba55be82decbfce3c359b58646ed2cd03000ad) `refactor(tests): mirror operator and renderer contract ownership`
- [`ba7f61b26107`](https://github.com/Entif-AI/Bilqis-MLX/commit/ba7f61b261076a3122c2f952a4ee45206c00af3c) `refactor(tests): group integration recovery and teaching contracts`
- [`c26719effe59`](https://github.com/Entif-AI/Bilqis-MLX/commit/c26719effe59c217645708908e2f9ff42f996453) `refactor(tests): separate causal teacher fixture and contracts`
- [`f09fa3dfaf61`](https://github.com/Entif-AI/Bilqis-MLX/commit/f09fa3dfaf61092fb24180d19c994caec8754c23) `refactor(tests): split retention teaching and mentor evidence`
- [`bbb2255e1ada`](https://github.com/Entif-AI/Bilqis-MLX/commit/bbb2255e1ada9a0232e94f14c29fc7de03718b35) `refactor(errors): split catalog by owning boundary`
- [`43b2c0d30791`](https://github.com/Entif-AI/Bilqis-MLX/commit/43b2c0d307915af0ea79541ff104968e1250199f) `fix(presentation): keep module CLI free of facade import cycles`
- [`1007c5412920`](https://github.com/Entif-AI/Bilqis-MLX/commit/1007c5412920f831d701317d467b8e042818d87b) `feat(presentation): stage source-bound BAMF cockpit observations`
- [`fd278789ac9a`](https://github.com/Entif-AI/Bilqis-MLX/commit/fd278789ac9a1336325170258a990dfa9b5ce991) `fix(ci): restore truthful BAMF portable verification`
- [`b63a65e91412`](https://github.com/Entif-AI/Bilqis-MLX/commit/b63a65e91412f5cfc945eccc3d060b8ed60707fe) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into sweep/pr633-20261031`
- [`a1392726589b`](https://github.com/Entif-AI/Bilqis-MLX/commit/a1392726589bc04998d4bb889b5d53cd8f53f7f1) `refactor(runtime): split state DAG ownership`
- [`f8265e1dbca2`](https://github.com/Entif-AI/Bilqis-MLX/commit/f8265e1dbca2d7d8ec1f9c1aa74602a52502e447) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into sweep/pr630-20261031`
- [`f8dac2dbbc80`](https://github.com/Entif-AI/Bilqis-MLX/commit/f8dac2dbbc80db55b5daaa4981d88bc91b2e2250) `docs(bamf): refresh A07 parent closeout evidence`
- [`63b1acd191a2`](https://github.com/Entif-AI/Bilqis-MLX/commit/63b1acd191a2ea40d17878551954d1730eef7577) `fix(runtime): preserve state DAG durable seam`
- [`6c64be280816`](https://github.com/Entif-AI/Bilqis-MLX/commit/6c64be2808165aa5e7bac181a0df3bccb4193cb1) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into sweep/pr644-20261031`
- [`83701b10098e`](https://github.com/Entif-AI/Bilqis-MLX/commit/83701b10098e26c24020d2d243526ff16cece54b) `refactor(runtime): split data plane ownership`
- [`20bcd3fc8d48`](https://github.com/Entif-AI/Bilqis-MLX/commit/20bcd3fc8d48e3020cf5f737eab01c1b9bb86c61) `refactor(quality): split operator contract scanner`
- [`86e04e95a451`](https://github.com/Entif-AI/Bilqis-MLX/commit/86e04e95a451da3a06bff3da60a900c24658ae18) `fix(runtime): preserve structural CLI help`
- [`840069077af3`](https://github.com/Entif-AI/Bilqis-MLX/commit/840069077af3ae8432d9b5020ac2dae5ab25971c) `style(runtime): clean data plane file endings`
- [`18c25b8c92a0`](https://github.com/Entif-AI/Bilqis-MLX/commit/18c25b8c92a009a661b858888269d181e7ae30fe) `refactor(quality): isolate operator scan constants`
- [`6cf92e71a728`](https://github.com/Entif-AI/Bilqis-MLX/commit/6cf92e71a7284fc71d61a9a24202386be0f481c3) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into HEAD`
- [`aa083208f40f`](https://github.com/Entif-AI/Bilqis-MLX/commit/aa083208f40f536859882973774174eb9fe6d41e) `refactor(factory): split curriculum compiler ownership`
- [`714ecf7dfea0`](https://github.com/Entif-AI/Bilqis-MLX/commit/714ecf7dfea058c2030a4d1681a56dfc4a4e764a) `fix(runtime): preserve public module identities`
- [`413ba0a169e1`](https://github.com/Entif-AI/Bilqis-MLX/commit/413ba0a169e1e0bd038bb2d9330ff571cc0b1119) `fix(factory): remove compiler owner import cycle`
- [`13523f9e4016`](https://github.com/Entif-AI/Bilqis-MLX/commit/13523f9e401662fd86d5014a03e7883fd6cb8c72) `refactor(semantics): split registry AST ownership`
- [`95be4d7d7660`](https://github.com/Entif-AI/Bilqis-MLX/commit/95be4d7d766052f042bdd91238e82f13a59e047d) `style(runtime): clean state DAG file endings`
- [`af5b49d2824f`](https://github.com/Entif-AI/Bilqis-MLX/commit/af5b49d2824f08d7daf6bc6e890fd98d717a4165) `fix(factory): preserve compiler type introspection`
- [`7efd4439604f`](https://github.com/Entif-AI/Bilqis-MLX/commit/7efd4439604f77f54e810be661bc941c218b91c6) `fix(quality): make operator-contract relocation accounting truthful`
- [`ba80882cfc66`](https://github.com/Entif-AI/Bilqis-MLX/commit/ba80882cfc668fe03898c8aa773e1e29ef548e1e) `fix(semantics): preserve registry public seams`
- [`13bb283dc376`](https://github.com/Entif-AI/Bilqis-MLX/commit/13bb283dc376f59bb81bbc3aedf9bf25f14fd545) `docs(bamf): refresh A07 parent closeout evidence`
- [`a02458cea060`](https://github.com/Entif-AI/Bilqis-MLX/commit/a02458cea06063a0e0a751306dd9d54f2c8ca389) `feat(bamf): enforce B10.3 causal typed-decoder feedback`
- [`e6ce18d4bccb`](https://github.com/Entif-AI/Bilqis-MLX/commit/e6ce18d4bccbc15e21003baafc2f4f46556a3bcc) `docs(bamf): record registry review repairs`
- [`bda9c7013816`](https://github.com/Entif-AI/Bilqis-MLX/commit/bda9c7013816651142e4e64d0fefefadc66cd300) `ci: avoid duplicate portable checks on codex branches`
- [`e3ea01776f5f`](https://github.com/Entif-AI/Bilqis-MLX/commit/e3ea01776f5f2610a140b780cef81680ae39482a) `Merge pull request #650 from Entif-AI/fix/ci-portable-event-baseline-649`
- [`f0ecc3f6031f`](https://github.com/Entif-AI/Bilqis-MLX/commit/f0ecc3f6031f2e227134dc0745cfcce9fe4230c4) `chore(bamf): refresh B03.3 from unified after CI repair`
- [`9ab0eb9fd31f`](https://github.com/Entif-AI/Bilqis-MLX/commit/9ab0eb9fd31f1cabb825a478adbd17864d74f5a4) `test(bamf): qualify B03.3 nested handles and compiler counts`
- [`3b5405c4b76f`](https://github.com/Entif-AI/Bilqis-MLX/commit/3b5405c4b76f53b7e2ed6af635dccb9e1b835e56) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into sweep/pr634-20261031`
- [`dd4ae9cd9233`](https://github.com/Entif-AI/Bilqis-MLX/commit/dd4ae9cd92334415d0032e628418bc4e61844df8) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into HEAD`
- [`0602fb336064`](https://github.com/Entif-AI/Bilqis-MLX/commit/0602fb336064b9971a50e22fc42245d92033ee12) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into HEAD`
- [`c8c5816397b3`](https://github.com/Entif-AI/Bilqis-MLX/commit/c8c5816397b37e2404e05afd5a02495211e02d23) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into HEAD`
- [`ecbe1f6e4441`](https://github.com/Entif-AI/Bilqis-MLX/commit/ecbe1f6e4441471aaa944361e65fe90f52622ecf) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into HEAD`
- [`c13070b49977`](https://github.com/Entif-AI/Bilqis-MLX/commit/c13070b49977acccc3c44f41d0df29984ca39818) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into HEAD`
- [`9e0d2456b128`](https://github.com/Entif-AI/Bilqis-MLX/commit/9e0d2456b1281fd131a12cd1add0e7e5ee0fd5ac) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into HEAD`
- [`6b00f6628e31`](https://github.com/Entif-AI/Bilqis-MLX/commit/6b00f6628e310f3d78c851cd9c94c25c8ede3221) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into HEAD`
- [`7a1682b7452a`](https://github.com/Entif-AI/Bilqis-MLX/commit/7a1682b7452aa1a63b6095fcd25c7d1b85755aa2) `docs(bamf): refresh B10.4 integrated prerequisite receipt`
- [`e979e4842f4b`](https://github.com/Entif-AI/Bilqis-MLX/commit/e979e4842f4b0831d57be33206dff542a4d648bd) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into HEAD`
- [`cec6a8ee1659`](https://github.com/Entif-AI/Bilqis-MLX/commit/cec6a8ee1659854c292dc59566d4d14a53b75ae5) `refactor(runtime): refresh C10.2 structural prerequisite`
- [`be8d4d60dc58`](https://github.com/Entif-AI/Bilqis-MLX/commit/be8d4d60dc5811041e9d9ae1c65f77f31750f183) `fix(bamf): name A09 frontier digest length`
- [`40f797f95c46`](https://github.com/Entif-AI/Bilqis-MLX/commit/40f797f95c46d367809a9e86676d25f79baed874) `refactor(runtime): refresh C10.2 structural prerequisite`
- [`61b4de07fac3`](https://github.com/Entif-AI/Bilqis-MLX/commit/61b4de07fac3e053f6c898a253415f51e4db4673) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into sweep/pr634-20261031`
- [`9a9f36ba91da`](https://github.com/Entif-AI/Bilqis-MLX/commit/9a9f36ba91da6f807e7129ba20041c0c600a7b13) `feat(bamf): refresh B14.1 rot3 cache coding`
- [`42a6a72409a6`](https://github.com/Entif-AI/Bilqis-MLX/commit/42a6a72409a68a4eebab912bec603186c18bc16d) `refactor(topology): refresh B01 tensor ownership split`
- [`431f6ef71252`](https://github.com/Entif-AI/Bilqis-MLX/commit/431f6ef712526c77c8641d32d9f2700e84e749fb) `feat(bamf): refresh A08 family authority`
- [`5071056af971`](https://github.com/Entif-AI/Bilqis-MLX/commit/5071056af97171f9d7b6f123d64f7d0101474fdb) `perf(ci): make semantic profile verification differential`
- [`4e32e369d9ed`](https://github.com/Entif-AI/Bilqis-MLX/commit/4e32e369d9ed55322dc1e52ef51f0c743a6e41cd) `fix(bamf): type A08 execution contract failures`
- [`339f360ae925`](https://github.com/Entif-AI/Bilqis-MLX/commit/339f360ae9258f5a1791144b765fef333d9d4c14) `fix(bamf): preserve A08 failures without catalog debt`
- [`a1a11ce7445f`](https://github.com/Entif-AI/Bilqis-MLX/commit/a1a11ce7445f6b8af409b48edf1f67ee352dde5b) `refactor(ci): split semantic test policy by responsibility`
- [`bea54bc1ddb4`](https://github.com/Entif-AI/Bilqis-MLX/commit/bea54bc1ddb41320394626aa86c26f98cd2f0d22) `feat(bamf): refresh B14.1 rot3 cache coding`
- [`354eda164f53`](https://github.com/Entif-AI/Bilqis-MLX/commit/354eda164f535ee925d21aab05021800a392b117) `fix(bamf): harden B14.1 codec integrity`
- [`55728d0bf78f`](https://github.com/Entif-AI/Bilqis-MLX/commit/55728d0bf78f21ca1234e9d4d56146de98587f6f) `chore(ci): refresh semantic profile work from unified`
- [`a11ae02cd03c`](https://github.com/Entif-AI/Bilqis-MLX/commit/a11ae02cd03c42ac4f2f68a3a63c81ac9fc8f6ae) `perf(ci): make semantic profile verification differential and sharded`
- [`14596c866be4`](https://github.com/Entif-AI/Bilqis-MLX/commit/14596c866be4445176b22266b9081dc9be790d53) `fix(bamf): harden merged B14.1 codec integrity`
- [`d790dc692a11`](https://github.com/Entif-AI/Bilqis-MLX/commit/d790dc692a11c052b7ee44a181aac54e8fb2585e) `feat(bamf): bind B10.4 readout census to B01 ledger`
- [`29429a3cbe18`](https://github.com/Entif-AI/Bilqis-MLX/commit/29429a3cbe18b66fe1b753443b02e3cd9a3c5450) `Merge commit 'd790dc692a11c052b7ee44a181aac54e8fb2585e' into HEAD`
- [`c04587197d4d`](https://github.com/Entif-AI/Bilqis-MLX/commit/c04587197d4d6ee7db9e3f07d0078dcfb3533202) `Merge commit 'd790dc692a11c052b7ee44a181aac54e8fb2585e' into HEAD`
- [`6a3819cf2e8c`](https://github.com/Entif-AI/Bilqis-MLX/commit/6a3819cf2e8cf127dc6c2028f34b7086ac66e5f2) `Merge commit 'd790dc692a11c052b7ee44a181aac54e8fb2585e' into HEAD`
- [`91f1496fdea1`](https://github.com/Entif-AI/Bilqis-MLX/commit/91f1496fdea1c05c82e07bc3cf0601228446ee0a) `Merge commit 'd790dc692a11c052b7ee44a181aac54e8fb2585e' into HEAD`
- [`a55a7c85344b`](https://github.com/Entif-AI/Bilqis-MLX/commit/a55a7c85344b08c486fbdb1ed460eb3bb1ea9b01) `fix(bamf): keep B01 replacement scope-clean`
- [`394252db8d8b`](https://github.com/Entif-AI/Bilqis-MLX/commit/394252db8d8b06c7059cfc2452ee097393abf75e) `Merge commit 'd790dc692a11c052b7ee44a181aac54e8fb2585e' into HEAD`
- [`521e92cad21d`](https://github.com/Entif-AI/Bilqis-MLX/commit/521e92cad21dafc4eecd42b473dc998b31e08ef8) `Merge commit 'd790dc692a11c052b7ee44a181aac54e8fb2585e' into HEAD`
- [`b16759f57ced`](https://github.com/Entif-AI/Bilqis-MLX/commit/b16759f57cedd8b58e0eb7ce814c131db8a84e7b) `chore(ci): refresh A08 semantic profile receipt`
- [`5747208a1b55`](https://github.com/Entif-AI/Bilqis-MLX/commit/5747208a1b5516a282f24221c0870498ae39bee4) `Merge commit 'd790dc692a11c052b7ee44a181aac54e8fb2585e' into HEAD`
- [`8f1b3346a00b`](https://github.com/Entif-AI/Bilqis-MLX/commit/8f1b3346a00b6b6f7992bb0369e2cecab870ab02) `Merge commit 'd790dc692a11c052b7ee44a181aac54e8fb2585e' into HEAD`
- [`46b6b0138802`](https://github.com/Entif-AI/Bilqis-MLX/commit/46b6b0138802876342f14bc0f0c59d4969b086d6) `Merge commit 'd790dc692a11c052b7ee44a181aac54e8fb2585e' into HEAD`
- [`3e69270b7144`](https://github.com/Entif-AI/Bilqis-MLX/commit/3e69270b71448356cd03002270390af447ba3331) `fix(bamf): name B10.5 decoder input invariants`
- [`8022d61d5316`](https://github.com/Entif-AI/Bilqis-MLX/commit/8022d61d5316c9bcc8ca7913959f292df3cc99ae) `fix(ci): install semantic ABI dependencies`
- [`4bac5323701d`](https://github.com/Entif-AI/Bilqis-MLX/commit/4bac5323701d198a6782b424cd5e24633b337b56) `fix(ci): install Semantic ABI integrity dependencies`
- [`20421845b58b`](https://github.com/Entif-AI/Bilqis-MLX/commit/20421845b58bc2d44646069437e6722c3ec013cf) `Merge commit 'd790dc692a11c052b7ee44a181aac54e8fb2585e' into HEAD`
- [`9e9aa9bd9eea`](https://github.com/Entif-AI/Bilqis-MLX/commit/9e9aa9bd9eea835b9865fdc878682507a0e8c7db) `Merge commit '4bac5323701d198a6782b424cd5e24633b337b56' into HEAD`
- [`660b5313a126`](https://github.com/Entif-AI/Bilqis-MLX/commit/660b5313a12639ffd6c88b06e39bd691d2f27db1) `Merge commit '4bac5323701d198a6782b424cd5e24633b337b56' into HEAD`
- [`0bbae3d71bf5`](https://github.com/Entif-AI/Bilqis-MLX/commit/0bbae3d71bf5710bb31dc317031a1f4b62b213b2) `Merge commit '4bac5323701d198a6782b424cd5e24633b337b56' into HEAD`
- [`b95caa59af87`](https://github.com/Entif-AI/Bilqis-MLX/commit/b95caa59af878e952523052c82ea5255fab9ea07) `Merge commit '4bac5323701d198a6782b424cd5e24633b337b56' into HEAD`
- [`f59a105a7f8c`](https://github.com/Entif-AI/Bilqis-MLX/commit/f59a105a7f8c96e3eb582121735ccf2d15b7307b) `Merge commit '4bac5323701d198a6782b424cd5e24633b337b56' into HEAD`
- [`952e04b2f231`](https://github.com/Entif-AI/Bilqis-MLX/commit/952e04b2f2310658b2f485f9d0ec18ea0b65239d) `Merge commit '4bac5323701d198a6782b424cd5e24633b337b56' into HEAD`
- [`7c9c21a17981`](https://github.com/Entif-AI/Bilqis-MLX/commit/7c9c21a17981ac9071c1ac5115844e343fd474fd) `Merge commit '4bac5323701d198a6782b424cd5e24633b337b56' into HEAD`
- [`a6e5d4dd2d5c`](https://github.com/Entif-AI/Bilqis-MLX/commit/a6e5d4dd2d5cc460dc8853ce2e59857500739a28) `Merge commit '4bac5323701d198a6782b424cd5e24633b337b56' into HEAD`
- [`531a8669c4df`](https://github.com/Entif-AI/Bilqis-MLX/commit/531a8669c4dfc2ab92bac66f339c0bd0cec9510e) `Merge commit '4bac5323701d198a6782b424cd5e24633b337b56' into HEAD`
- [`2d3a31235aa5`](https://github.com/Entif-AI/Bilqis-MLX/commit/2d3a31235aa57ee206da73561a206ba67f100f13) `Merge commit '4bac5323701d198a6782b424cd5e24633b337b56' into HEAD`
- [`f8364b83a41e`](https://github.com/Entif-AI/Bilqis-MLX/commit/f8364b83a41e99ee744d794f6a6b6eaf1f71a92b) `fix(bamf): preserve B01 adapter category ownership`
- [`154cd0ce29e4`](https://github.com/Entif-AI/Bilqis-MLX/commit/154cd0ce29e42512500c680e76e5a5313324aac4) `fix(ci): scope Semantic ABI checks to PR changes`
- [`a6bb632750e2`](https://github.com/Entif-AI/Bilqis-MLX/commit/a6bb632750e26dd6a3e73395e0d1904e1142bf74) `docs(bamf): refresh A08.1b.5 evidence receipt`
- [`b6851e52a2b8`](https://github.com/Entif-AI/Bilqis-MLX/commit/b6851e52a2b882d2699623a95ad27c1fac0f58b9) `refactor(tests): group runtime model witnesses`
- [`ea0effe1ece9`](https://github.com/Entif-AI/Bilqis-MLX/commit/ea0effe1ece91491b67aefff8f28e714d4ed41a7) `fix(ci): follow relocated topology witness`
- [`9be3df49b590`](https://github.com/Entif-AI/Bilqis-MLX/commit/9be3df49b590370a085449880f92235fec44dc0f) `fix(ci): emit base-relative Semantic ABI status`
- [`874f4183ebfc`](https://github.com/Entif-AI/Bilqis-MLX/commit/874f4183ebfca3f3754b31d7df1c155e6480d25a) `fix(ci): cover split semantic owners`
- [`4e1ba1c9bdb4`](https://github.com/Entif-AI/Bilqis-MLX/commit/4e1ba1c9bdb4af262ce3ff305f3831d693890a9d) `refactor(presentation): clear changed-file smell debt`
- [`aedeff542d61`](https://github.com/Entif-AI/Bilqis-MLX/commit/aedeff542d61f0bfd46dc517d44b85ef187aaec9) `refactor(topology): refresh B01 tensor ownership split`
- [`351a7f69ede0`](https://github.com/Entif-AI/Bilqis-MLX/commit/351a7f69ede047b9678c095864e4ba324acc4a0e) `fix(bamf): refresh A08 execution and source authority`
- [`c6ee2d8386af`](https://github.com/Entif-AI/Bilqis-MLX/commit/c6ee2d8386afd7daa2164da64f967fa38f9f0c4a) `fix(ci): scope Semantic ABI checks to PR changes`
- [`e63a994b6e63`](https://github.com/Entif-AI/Bilqis-MLX/commit/e63a994b6e63179eff92f3c388bf567f2cf4e65d) `refactor(tests): group runtime model witnesses`
- [`7c9d756f072e`](https://github.com/Entif-AI/Bilqis-MLX/commit/7c9d756f072e23898fc3b8f805da7427c01e7683) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into fix/bamf-a09-1a-refresh-e63a`
- [`874aef7f42b5`](https://github.com/Entif-AI/Bilqis-MLX/commit/874aef7f42b5b195de725b481f138fedd7fcf270) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into fix/bamf-b10-5-refresh-e63a`
- [`c0e92894fe17`](https://github.com/Entif-AI/Bilqis-MLX/commit/c0e92894fe1703d17f9417b5e219da6237aa1050) `refactor(ci): extract factory architecture inspection rules`
- [`23ccf2e65451`](https://github.com/Entif-AI/Bilqis-MLX/commit/23ccf2e65451f82790fbce99784c84441ebcecb7) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into fix/bamf-b08-1-refresh-e63a`
- [`714e9dc1ee22`](https://github.com/Entif-AI/Bilqis-MLX/commit/714e9dc1ee2234923d65c683c5a44d5f49627ff6) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into fix/bamf-b12-2-refresh-e63a`
- [`e0abfd190f1a`](https://github.com/Entif-AI/Bilqis-MLX/commit/e0abfd190f1a1b60de529acdbe892987863cebf0) `refactor(tests): group runtime model witnesses by responsibility`
- [`aac9dc165f0d`](https://github.com/Entif-AI/Bilqis-MLX/commit/aac9dc165f0d47d9dfe5f65d03e2879a98d407f1) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into fix/bamf-c11-2-refresh-e63a`
- [`194a07710533`](https://github.com/Entif-AI/Bilqis-MLX/commit/194a0771053346fc63b14d72bb2d238b6e10ef5d) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into fix/bamf-b11-refresh-e63a`
- [`6f2bfd643a28`](https://github.com/Entif-AI/Bilqis-MLX/commit/6f2bfd643a2855511fe9601ec7b1df071aa5058c) `docs(errors): refresh model test path in generated catalog`
- [`53b3d3a6b784`](https://github.com/Entif-AI/Bilqis-MLX/commit/53b3d3a6b7845b61d04ef02111b465f4512695dc) `docs(errors): refresh generated manual after module relocation`
- [`15c0850cf866`](https://github.com/Entif-AI/Bilqis-MLX/commit/15c0850cf8668552b858c28c7673746acb0b6931) `fix(semantics): restore source adapter dependency boundary`
- [`7df71fb01cef`](https://github.com/Entif-AI/Bilqis-MLX/commit/7df71fb01cef068676d3b9cd2fb41fd8adc35798) `Merge commit 'e63a994b6e63179eff92f3c388bf567f2cf4e65d' into fix/pr620-model-tests-worker2-20261031`
- [`311e82b6adee`](https://github.com/Entif-AI/Bilqis-MLX/commit/311e82b6adee03c107fb42ab0a42a64d26c1b515) `Merge commit 'e63a994b6e63179eff92f3c388bf567f2cf4e65d' into fix/pr632-c11-integration-worker2-20261031`
- [`0f9caf407d50`](https://github.com/Entif-AI/Bilqis-MLX/commit/0f9caf407d508443f26d332bf158e4e4e7482e3a) `refactor(ci): compartmentalize Ithkuil skill packaging entrypoint`
- [`6d23d7838057`](https://github.com/Entif-AI/Bilqis-MLX/commit/6d23d783805718c1019c9084837086acb43500be) `fix(ci): resolve relocated ABI tests and numeric error contracts`
- [`aa84b67da5ad`](https://github.com/Entif-AI/Bilqis-MLX/commit/aa84b67da5ad46e609f5471a56e581ff19370ae7) `Revert "refactor(ci): compartmentalize Ithkuil skill packaging entrypoint"`
- [`56fd0c346b99`](https://github.com/Entif-AI/Bilqis-MLX/commit/56fd0c346b999bdb8cf62d946848295ae7fc7f81) `refactor(ci): compartmentalize qualification freezing helper`
- [`15eafa3c185d`](https://github.com/Entif-AI/Bilqis-MLX/commit/15eafa3c185d123d5d0043ec9078752b4b44e28b) `refactor(runtime): split checkpoint custody facade`
- [`011e17b483ec`](https://github.com/Entif-AI/Bilqis-MLX/commit/011e17b483ecd6abc35680f8ee8d92d19924789b) `fix(semantics): freeze source node dispatch mapping`
- [`2d2b0704b2fd`](https://github.com/Entif-AI/Bilqis-MLX/commit/2d2b0704b2fd5bfecb413519987e7589b12b18ea) `test(a09): verify planner against pinned real A08 frontier`
- [`79b9982ecb75`](https://github.com/Entif-AI/Bilqis-MLX/commit/79b9982ecb75f4ff0822cd6bc88ebdc791fbb7a5) `refactor(runtime): isolate BAMF bundle codec`
- [`4e21bd72b000`](https://github.com/Entif-AI/Bilqis-MLX/commit/4e21bd72b00073cfd08893967c14a78640de7498) `fix(b10): require decoder-issued logits for supervised loss`
- [`7111e7c5e7fa`](https://github.com/Entif-AI/Bilqis-MLX/commit/7111e7c5e7fada9bdf6261668bcc85d69fe927ea) `fix(runtime): revalidate C10.3 staging proofs and cold reads`
- [`c577a0ee05e9`](https://github.com/Entif-AI/Bilqis-MLX/commit/c577a0ee05e9f187fa767b67c1819d5c725ff4ea) `feat(runtime): checkpoint BAMF v2 bundle custody`
- [`4a2a5858c6b8`](https://github.com/Entif-AI/Bilqis-MLX/commit/4a2a5858c6b85e9627f2e8af6d300296ddb96b42) `feat(bamf): stage in-memory B12.2 candidate custody`
- [`a879ae211c80`](https://github.com/Entif-AI/Bilqis-MLX/commit/a879ae211c80b4eac44adca33bdb57fad1d8fc1c) `fix(semantics): restore source adapter dependency boundary`
- [`d03e72a2ecc5`](https://github.com/Entif-AI/Bilqis-MLX/commit/d03e72a2ecc507704adda4a4735edd6f9688e693) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into fix/bamf-a09-1a-refresh-e63a`
- [`2cb244d2d14c`](https://github.com/Entif-AI/Bilqis-MLX/commit/2cb244d2d14ccf89afa5814b6bb2fd4de52389c8) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into feat/bamf-b13-1-bundle-20261031`
- [`2bbe081da7ca`](https://github.com/Entif-AI/Bilqis-MLX/commit/2bbe081da7ca09e49fc83121c51ad466171c4457) `fix(b10): snapshot issued decoder meaning before supervised loss`
- [`136b64d69268`](https://github.com/Entif-AI/Bilqis-MLX/commit/136b64d69268e0ae242487dbd17ed9fa1af1e25e) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into fix/bamf-c11-2-refresh-e63a`
- [`a9239a1bd1dd`](https://github.com/Entif-AI/Bilqis-MLX/commit/a9239a1bd1dd24a3a1b27ee78b7772d5354b92f1) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into fix/bamf-b08-1-refresh-e63a`
- [`385cadd379a7`](https://github.com/Entif-AI/Bilqis-MLX/commit/385cadd379a7039781ab9de6589c01f4e35a0ef8) `feat(runtime): complete BAMF generation custody`
- [`35944b3405f5`](https://github.com/Entif-AI/Bilqis-MLX/commit/35944b3405f57bab11f3e51875a0feeb82252353) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into fix/bamf-b11-refresh-e63a`
- [`edf854c5144f`](https://github.com/Entif-AI/Bilqis-MLX/commit/edf854c5144f1d951b4edbedc8dcd5bf05ef9c5a) `fix(b10): encapsulate ephemeral decoder issuance registry`
- [`edaed7e0f1c1`](https://github.com/Entif-AI/Bilqis-MLX/commit/edaed7e0f1c1385ecc09788d363074a5f3f2847d) `Merge commit 'a879ae211c80b4eac44adca33bdb57fad1d8fc1c' into fix/bamf-b10-5-refresh-e63a`
- [`bccd4ae1cbe3`](https://github.com/Entif-AI/Bilqis-MLX/commit/bccd4ae1cbe3684f3c80ac1a91752cff77ac355b) `fix(runtime): centralize BAMF motif error code`
- [`57443920a417`](https://github.com/Entif-AI/Bilqis-MLX/commit/57443920a4174ed345240d59c862ce30d4ef48c5) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into fix/pr632-c11-integration-worker2-20261031`
- [`dd6a68792df0`](https://github.com/Entif-AI/Bilqis-MLX/commit/dd6a68792df0cfcdd7eff1f9c0ca2d4a3cc53509) `test(runtime): prove rejection cold-resume custody`
- [`9e6287e1b7a3`](https://github.com/Entif-AI/Bilqis-MLX/commit/9e6287e1b7a3982d6b6e969b057e02b14106bd76) `fix(bamf): rebuild A09.1a clean turn-in`
- [`dea8b2338cd4`](https://github.com/Entif-AI/Bilqis-MLX/commit/dea8b2338cd42de7028e80cab3618da447836544) `feat(presentation): stage truthful BAMF cockpit observations`
- [`39fd5c9f6151`](https://github.com/Entif-AI/Bilqis-MLX/commit/39fd5c9f615185d508c632503a18d827fa0a1015) `docs(errors): regenerate C11 merged owner locations`
- [`fd2a4556b4e4`](https://github.com/Entif-AI/Bilqis-MLX/commit/fd2a4556b4e460256df086b2f9ce9cdbeb0f1c86) `style(quality): remove trailing architecture helper blank lines`
- [`032d24cfdfd2`](https://github.com/Entif-AI/Bilqis-MLX/commit/032d24cfdfd288fd91c4c183ea5d3a11e5ad7896) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into fix/pr632-c11-integration-worker2-20261031`
- [`0081912578b6`](https://github.com/Entif-AI/Bilqis-MLX/commit/0081912578b6ef1bd43a1416aae42453e6201703) `test(c11): patch relocated CLI execution owners`
- [`ae5b030da7cb`](https://github.com/Entif-AI/Bilqis-MLX/commit/ae5b030da7cbfec250fc88fc0d93e8dddddf05cd) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into fix/bamf-b08-1-refresh-e63a`
- [`395fe5adee4a`](https://github.com/Entif-AI/Bilqis-MLX/commit/395fe5adee4a1049ef7623d27d401f8f25abd53c) `Merge commit 'dea8b2338cd42de7028e80cab3618da447836544' into fix/bamf-b10-5-refresh-e63a`
- [`c84d0f40c8dc`](https://github.com/Entif-AI/Bilqis-MLX/commit/c84d0f40c8dc832d325fb047c1c3a341b7243483) `fix(b10): fingerprint issued logits against in-place mutation`
- [`b0b015cfbd47`](https://github.com/Entif-AI/Bilqis-MLX/commit/b0b015cfbd4744fa84ec0358aa0196e01a9634dc) `fix(quality): resolve historical physical owners in smell baselines`
- [`ca9deab51e8e`](https://github.com/Entif-AI/Bilqis-MLX/commit/ca9deab51e8edd9a6f40a440f75d3606e21d18ac) `feat(bamf): stage source-bound motif gate features and preserve read quarantine`
- [`6af24600a4e8`](https://github.com/Entif-AI/Bilqis-MLX/commit/6af24600a4e8861774b71f456a7d59b41cb87569) `fix(quality): honor relocated physical owners in hygiene delta baseline`
- [`ab25ed5bea40`](https://github.com/Entif-AI/Bilqis-MLX/commit/ab25ed5bea40ba23e32e8e95bd55c40365954a1d) `Merge commit '6af24600a4e8861774b71f456a7d59b41cb87569' into fix/bamf-b11-refresh-e63a`
- [`0edf5ad24ad1`](https://github.com/Entif-AI/Bilqis-MLX/commit/0edf5ad24ad181398e7465441af7381ad0569713) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into fix/pr632-c11-integration-worker2-20261031`
- [`4694a98660fd`](https://github.com/Entif-AI/Bilqis-MLX/commit/4694a98660fdc67ab15b6cb4d5212ece531a0c85) `fix(quality): restrict physical-owner debt fallback to renames`
- [`33cdda36feb4`](https://github.com/Entif-AI/Bilqis-MLX/commit/33cdda36feb4e6cfd0a4b5c33ad69647886dc9fc) `test(learning): honor two tracked teaching compatibility symlinks`
- [`39211d54fa96`](https://github.com/Entif-AI/Bilqis-MLX/commit/39211d54fa9626dd5fd4201d5eb0641f20109b3c) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into fix/bamf-b10-5-refresh-e63a`
- [`9cf6f3058183`](https://github.com/Entif-AI/Bilqis-MLX/commit/9cf6f3058183d555710d7512068858343ce87f84) `test(learning): verify only tracked teaching compatibility symlinks`
- [`59af2930985c`](https://github.com/Entif-AI/Bilqis-MLX/commit/59af2930985c68609cad92f57ad2b711807742ff) `fix(quality): restrict relocated debt fallback to renames`
- [`7296eef9da0d`](https://github.com/Entif-AI/Bilqis-MLX/commit/7296eef9da0dfe58eeb46b26c3410a6ba519d797) `feat(bamf): compose bounded typed prediction and masked answer loss`
- [`3d8ee29b6c26`](https://github.com/Entif-AI/Bilqis-MLX/commit/3d8ee29b6c267fceccd53bac9999993c814c3539) `test(learning): inventory approved compatibility symlinks`
- [`13d8106e62dd`](https://github.com/Entif-AI/Bilqis-MLX/commit/13d8106e62dd6ae3c3d0cafd6bd958c651c88707) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into fix/bamf-source-atoms-layout-contract-20261031`
- [`c63b07aba353`](https://github.com/Entif-AI/Bilqis-MLX/commit/c63b07aba353a475fe5870066edc92c9d008f551) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into fix/pr632-c11-integration-worker2-20261031`
- [`445ef2df7a1a`](https://github.com/Entif-AI/Bilqis-MLX/commit/445ef2df7a1ac87378efd34b2437bcdef02a8251) `test(learning): inventory approved compatibility symlinks`
- [`bb626d75eb0e`](https://github.com/Entif-AI/Bilqis-MLX/commit/bb626d75eb0e7d5a8efbb9c0ac10d37cf038e197) `docs(adr): clarify issue closeout and regression lifecycle`
- [`e73e9478e39d`](https://github.com/Entif-AI/Bilqis-MLX/commit/e73e9478e39db51c1349da8b0bbd6ef9209c68d8) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/bamf02-b-neural`
- [`783355bbf3c7`](https://github.com/Entif-AI/Bilqis-MLX/commit/783355bbf3c7c22317e089e7bf3cf299b78532c8) `feat(bamf): restore stable norm blocks and FP32 cache fallback`
- [`30385b0f245e`](https://github.com/Entif-AI/Bilqis-MLX/commit/30385b0f245e820657b8c8e71f762eb6f9c0e40e) `feat(bamf): stage portable cognitive package manifests`
- [`4ab8c5daf52c`](https://github.com/Entif-AI/Bilqis-MLX/commit/4ab8c5daf52c31801e336b3727f53fe963622924) `feat(bamf): restore stable norm blocks and FP32 cache fallback`
- [`7a736102c6e9`](https://github.com/Entif-AI/Bilqis-MLX/commit/7a736102c6e9a19640ee7180421f837880c13b14) `fix(cockpit): show current assessment policy and historical lineage`
- [`32dea836b560`](https://github.com/Entif-AI/Bilqis-MLX/commit/32dea836b560ccbf5e194acc7fe4fe34cb32d187) `refactor(runtime): group cache and backbone owners below directory limit`
- [`21ef50cdc87c`](https://github.com/Entif-AI/Bilqis-MLX/commit/21ef50cdc87c9d54a3121be1029842356c3c88f5) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/bamf02-a-sync-20261101`
- [`469465b2b72b`](https://github.com/Entif-AI/Bilqis-MLX/commit/469465b2b72b76546076845ece1e1546061996e6) `feat(bamf): bind cache records and enforce FP32 fallback policy`
- [`2dc2e831bcda`](https://github.com/Entif-AI/Bilqis-MLX/commit/2dc2e831bcdabe90933a7cc8b5fc5d0d9f58c87c) `fix(bamf): reuse canonical cache head width in validation`
- [`f438b3015df3`](https://github.com/Entif-AI/Bilqis-MLX/commit/f438b3015df3e312329f337f02a58192d4c25de9) `test(bamf): use native unittest failure for stale cache guard`
- [`f7a46f0c2e8d`](https://github.com/Entif-AI/Bilqis-MLX/commit/f7a46f0c2e8d4a454568feb5fc661b004da1b0d4) `feat(cockpit): separate operator evidence and complete snapshots`
- [`1dc9ed378a85`](https://github.com/Entif-AI/Bilqis-MLX/commit/1dc9ed378a855b99cfa91e523b661da6c749dd7e) `refactor(factory): split candidate frontier IO before A09 reconciliation`
- [`7303d0d0b2af`](https://github.com/Entif-AI/Bilqis-MLX/commit/7303d0d0b2afbbc35cf2085ba3a3437fbdca3554) `feat(bamf): reconcile qualified A09 curriculum events`
- [`86a831fbdb68`](https://github.com/Entif-AI/Bilqis-MLX/commit/86a831fbdb68043e9949c4d63721b64580a993b1) `fix(bamf): bind A09 events to source provenance`
- [`eead4400d2a5`](https://github.com/Entif-AI/Bilqis-MLX/commit/eead4400d2a57467d45ea482163eb8898c6bddf7) `Merge remote-tracking branch 'origin/feat/bamf-b13-1-bundle-20261031' into codex/bamf02-b13-478-custody-20261101`
- [`522d2f7c2afe`](https://github.com/Entif-AI/Bilqis-MLX/commit/522d2f7c2afe4153e7144883da49400d49c699bf) `test(runtime): reproduce BAMF durability and outbox races`
- [`8f76ee906ac0`](https://github.com/Entif-AI/Bilqis-MLX/commit/8f76ee906ac00fbd94d00516e27d3f067d1e7b56) `fix(runtime): serialize BAMF delivery and fsync retained tensors`
- [`f1888a146b0e`](https://github.com/Entif-AI/Bilqis-MLX/commit/f1888a146b0e1925f7b830e88a0fc7e79b2464ae) `test(runtime): reject incomplete BAMF identity sidecars`
- [`ea76dc5bc093`](https://github.com/Entif-AI/Bilqis-MLX/commit/ea76dc5bc093174657a943ffa0a505c35c7f0285) `test(runtime): bind sidecar replay witness to generation lineage`
- [`7c4412241859`](https://github.com/Entif-AI/Bilqis-MLX/commit/7c44122418595fe542ee2ac80085aeead43ae5c8) `fix(runtime): require versioned BAMF identity sidecars`
- [`f183175cb022`](https://github.com/Entif-AI/Bilqis-MLX/commit/f183175cb022190fe8333414627b6854f4598af2) `fix(errors): register checkpoint custody recovery contracts`
- [`3e1647fe2c91`](https://github.com/Entif-AI/Bilqis-MLX/commit/3e1647fe2c91d06773b4e66348554feb9b7a921b) `refactor(tests): compartmentalize curriculum frontier coverage`
- [`d71827c0e49a`](https://github.com/Entif-AI/Bilqis-MLX/commit/d71827c0e49a2e1b4e5e158c3e761e3f0f6d8126) `test(runtime): reject unowned outboxes and unsafe tensor entries`
- [`baafd5447758`](https://github.com/Entif-AI/Bilqis-MLX/commit/baafd5447758d12ce2579fb060b56c642e72bb94) `fix(runtime): validate generation ownership before tensor I/O`
- [`ff6d284535c2`](https://github.com/Entif-AI/Bilqis-MLX/commit/ff6d284535c25cab8de08d541a0d6efedaf00119) `docs(errors): refresh candidate frontier locations`
- [`117b20af1242`](https://github.com/Entif-AI/Bilqis-MLX/commit/117b20af1242bbd9f0090e05da46dd9b9f9816f7) `docs(bamf): record B13 custody repair proof and limits`
- [`f4bb11abfeb7`](https://github.com/Entif-AI/Bilqis-MLX/commit/f4bb11abfeb739e121a65895c992534d4e61f2f6) `docs(bamf): record complete affected custody verification`
- [`43e89de93b57`](https://github.com/Entif-AI/Bilqis-MLX/commit/43e89de93b578d77e0eed49304a6ca3368ca5202) `feat(bamf): restore stable B14.2 norm blocks and FP32 fallback`
- [`4fa27b42430b`](https://github.com/Entif-AI/Bilqis-MLX/commit/4fa27b42430b220e0ba07ed0dbf3f1a7d83dc6d4) `feat(bamf): reconcile qualified A09 curriculum events`
- [`ec3c765aea33`](https://github.com/Entif-AI/Bilqis-MLX/commit/ec3c765aea33503e2dfcc7c69caafc76583dd69b) `test(runtime): freeze BAMF sidecar schema fixtures`
- [`bd9ea2ce3ac4`](https://github.com/Entif-AI/Bilqis-MLX/commit/bd9ea2ce3ac4492dee3f3528787ede69931b2218) `chore(bamf): sync B13 custody with reviewed unified`
- [`75c71ec49630`](https://github.com/Entif-AI/Bilqis-MLX/commit/75c71ec49630df7d1ecf4a4c94ad0580947856d3) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/bamf02-a-sync-20261101`
- [`7d049ff38158`](https://github.com/Entif-AI/Bilqis-MLX/commit/7d049ff381583d33661faaf6b85c11ed523858b4) `fix(bamf): keep source events outside implementation authority`
- [`b9e1a20b37b7`](https://github.com/Entif-AI/Bilqis-MLX/commit/b9e1a20b37b79ac779b7b7a88715f2f93533d463) `chore(bamf): refresh B14.3 on reviewed unified`
- [`0d98c1930e55`](https://github.com/Entif-AI/Bilqis-MLX/commit/0d98c1930e55b8a911f0c498e761985aa292ae88) `Merge remote-tracking branch 'origin/codex/bamf02-b14-3-484-finish-20261101' into codex/bamf02-b14-4-485-refresh-20261101`
- [`b2fb8255a8aa`](https://github.com/Entif-AI/Bilqis-MLX/commit/b2fb8255a8aaa4f97fcfd35fdab92ce31d254453) `fix(bamf): validate source replay authority before idempotence`
- [`d6872978f869`](https://github.com/Entif-AI/Bilqis-MLX/commit/d6872978f869f0f0599076b128ba843e0f647dde) `feat(bamf): reject revoked cache and rebuild from fp32`
- [`48faae762bd2`](https://github.com/Entif-AI/Bilqis-MLX/commit/48faae762bd2942ff28633d075817c35db33f56b) `test(bamf): prove B14.4 cache replacement boundary`
- [`bd6c6e547c01`](https://github.com/Entif-AI/Bilqis-MLX/commit/bd6c6e547c01d1b1600ad41cdac42052dffecc1c) `docs(bamf): record B14.4 staged qualification`
- [`6ceda5a0b708`](https://github.com/Entif-AI/Bilqis-MLX/commit/6ceda5a0b7083a4648d37b1cd392bf1fc5e45445) `test(bamf): close B14.4 review proof gaps`
- [`0a869f43886f`](https://github.com/Entif-AI/Bilqis-MLX/commit/0a869f43886f1c3b019d9f963211af86dcfb1053) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/b11-586-refresh-20261101`
- [`ef38532c1f9d`](https://github.com/Entif-AI/Bilqis-MLX/commit/ef38532c1f9ddc4f142a342d29ef09e08d49c390) `feat(bamf): stage B14.3 cache binding and FP32 policy`
- [`db85d745c220`](https://github.com/Entif-AI/Bilqis-MLX/commit/db85d745c2202d6813361ffecf7562f548d41bec) `fix(bamf): keep A09 source events outside implementation authority`
- [`d9f9d4b0642d`](https://github.com/Entif-AI/Bilqis-MLX/commit/d9f9d4b0642dd7d840778c840ea7a2d0c5dc4b2f) `feat(bamf): resolve A09 typed prerequisite closure`
- [`dc2c56b920d3`](https://github.com/Entif-AI/Bilqis-MLX/commit/dc2c56b920d3a1a51fc2389a906f266cd41054be) `test(bamf): follow accepted A09 frontier test layout`
- [`c7f9d1cd35b0`](https://github.com/Entif-AI/Bilqis-MLX/commit/c7f9d1cd35b01f329c2f2123617f65e20dd22c0b) `fix(bamf): bind A09 prerequisite readiness to typed evidence`
- [`1bd71e97f008`](https://github.com/Entif-AI/Bilqis-MLX/commit/1bd71e97f0088c4ad70f1850ce485716d2fab083) `fix(bamf): verify A09 prerequisite evidence against current learner state`
- [`6f250d5e8823`](https://github.com/Entif-AI/Bilqis-MLX/commit/6f250d5e8823f289ac87154ee3051b6e81675ca6) `fix(bamf): derive prerequisite mastery from admitted semantic roots`
- [`604d2ee9be9f`](https://github.com/Entif-AI/Bilqis-MLX/commit/604d2ee9be9fa61ae4758399ffc74eba9291bb28) `feat(bamf): bind B11 producer receipts to executed backbone`
- [`d2eeeb0cd1db`](https://github.com/Entif-AI/Bilqis-MLX/commit/d2eeeb0cd1db59d1ec187d2c1f4bbab541ef7a4a) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/b11-586-refresh-20261101`
- [`7b5ef8273497`](https://github.com/Entif-AI/Bilqis-MLX/commit/7b5ef8273497daf6fa48de6adcc9333c18aa500e) `fix(bamf): name A09 digest length guard`
- [`d2bb818f8852`](https://github.com/Entif-AI/Bilqis-MLX/commit/d2bb818f8852b384aa969db9c46d5165715e2b0f) `fix(bamf): harden B11 producer receipt authority`
- [`6c86fcde8880`](https://github.com/Entif-AI/Bilqis-MLX/commit/6c86fcde8880f756e9a6e99216c351d4f3cfc441) `docs(bamf): record B11 producer qualification`
- [`613ea0dc5306`](https://github.com/Entif-AI/Bilqis-MLX/commit/613ea0dc53067f6618301d7e03b5cce18fc20a8c) `feat(bamf): resolve typed prerequisite closure (A09.2)`
- [`68e8524105d7`](https://github.com/Entif-AI/Bilqis-MLX/commit/68e8524105d754f61b142e234bef62c4e25aecfc) `refactor(bamf): split B11 producer and depth owners`
- [`f3c9f23d17bf`](https://github.com/Entif-AI/Bilqis-MLX/commit/f3c9f23d17bf3f850415cd953ab313406b64eab5) `feat(bamf): select bounded A09 curriculum deltas`
- [`9a2755ff5ab2`](https://github.com/Entif-AI/Bilqis-MLX/commit/9a2755ff5ab20ebbb2495b552665921c342e67d2) `fix(bamf): validate A09 closure reason ownership`
- [`94df45434768`](https://github.com/Entif-AI/Bilqis-MLX/commit/94df45434768244e87c0cfaf2024aeeb2d935974) `test(bamf): avoid A09 fixture error debt`
- [`65b50ea4949d`](https://github.com/Entif-AI/Bilqis-MLX/commit/65b50ea4949d0f0e36d2604faa67fb51d93186d9) `fix(bamf): bind B11 receipts to live execution authority`
- [`22df4350749a`](https://github.com/Entif-AI/Bilqis-MLX/commit/22df4350749a96ca7da77d8b0b6c6fcb5650858d) `test(bamf): preserve A09 cycle fixture semantics`
- [`75caef2fffc6`](https://github.com/Entif-AI/Bilqis-MLX/commit/75caef2fffc6449358c33f9070d9dfc9d6f90c3f) `docs(bamf): record repaired B11 producer authority`
- [`70e37ae27214`](https://github.com/Entif-AI/Bilqis-MLX/commit/70e37ae27214061dcc1712503eae6741a2e3781e) `feat(bamf): select bounded A09 curriculum deltas (#393)`
- [`4734a51f83d9`](https://github.com/Entif-AI/Bilqis-MLX/commit/4734a51f83d9e61f4166bf7116e5e5e698559f0f) `docs(bamf): ratify A09.4 projection custody`
- [`d5a94196d593`](https://github.com/Entif-AI/Bilqis-MLX/commit/d5a94196d5933c1a57e2514e8d37c79a806090ac) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/b11-586-refresh-20261101`
- [`1447cbcdc0c4`](https://github.com/Entif-AI/Bilqis-MLX/commit/1447cbcdc0c4c5b145281e0ce125ef26d1582d76) `refactor(bamf): compartmentalize atlas frontier`
- [`0346fc8e757e`](https://github.com/Entif-AI/Bilqis-MLX/commit/0346fc8e757e239d3a14130a7f0acac3d64bcc6d) `feat(bamf): port A09 frontier progress`
- [`10b2ef4ff2b3`](https://github.com/Entif-AI/Bilqis-MLX/commit/10b2ef4ff2b369b48b6e0b89006ef1daf5055e3a) `fix(bamf): bind A09 progress to exact projection`
- [`7242cf6a60e7`](https://github.com/Entif-AI/Bilqis-MLX/commit/7242cf6a60e7a671e9b93e749dbaceafb65e02e4) `fix(bamf): revalidate resumed frontier selections`
- [`ef0e803116f7`](https://github.com/Entif-AI/Bilqis-MLX/commit/ef0e803116f752c1eb706f08dc7ae460b2bcd6a5) `fix(bamf): seal B11 selected-state producer flow`
- [`4d349159c757`](https://github.com/Entif-AI/Bilqis-MLX/commit/4d349159c757195ff12ba20614c86f8c6ea80570) `fix(bamf): derive B11 receipts from producer execution`
- [`f0dd9ddeb5b3`](https://github.com/Entif-AI/Bilqis-MLX/commit/f0dd9ddeb5b374f6038b8de350b26cc56ea7e347) `fix(bamf): replay B11 receipt boundaries`
- [`ed647441a334`](https://github.com/Entif-AI/Bilqis-MLX/commit/ed647441a3346cddae537e8ea1a1e012403c14ff) `fix(bamf): authenticate replayed B11 receipts`
- [`6d1b2bdd417b`](https://github.com/Entif-AI/Bilqis-MLX/commit/6d1b2bdd417bcd56bdf49ff7cfdefee412c88f5f) `fix(bamf): bind resume comparator context`
- [`6ced8eff290f`](https://github.com/Entif-AI/Bilqis-MLX/commit/6ced8eff290f3e0ba44674acd4c780427e8ddf94) `fix(runtime): keep checkpoint metadata independent of MLX`
- [`ffe7cf078a78`](https://github.com/Entif-AI/Bilqis-MLX/commit/ffe7cf078a7807c8e9ac622887b7e0578777aa34) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/bamf02-c11-524-provenance-20261101`
- [`faf84da9ad41`](https://github.com/Entif-AI/Bilqis-MLX/commit/faf84da9ad419acab74a2210c80ae285c229e40a) `chore(bamf): refresh C11 CLI work from current Lane C`
- [`ac4bbc87e791`](https://github.com/Entif-AI/Bilqis-MLX/commit/ac4bbc87e7913c1563ef34c1e3ffea591d57a622) `test(bamf): specify held v2 operator preflight (#522)`
- [`006a4c559678`](https://github.com/Entif-AI/Bilqis-MLX/commit/006a4c55967807dd0428533842ab7fc3665f54d1) `feat(bamf): inspect v2 operator configuration without learner mutation (#522)`
- [`a538472acd26`](https://github.com/Entif-AI/Bilqis-MLX/commit/a538472acd26d08fd4d13d692fbf55204a5c9dd3) `test(bamf): expose recursive child census false results (#347)`
- [`776898fa8e6e`](https://github.com/Entif-AI/Bilqis-MLX/commit/776898fa8e6eac469c79b7a35ad0a51e1ef5d24a) `fix(bamf): keep recursive child census accurate and fail closed (#347)`
- [`7ec4665299be`](https://github.com/Entif-AI/Bilqis-MLX/commit/7ec4665299be732823745bde40f4e5042d393411) `chore(bamf): consume C12 manifest contract for local exchange (#526)`
- [`d183d617f295`](https://github.com/Entif-AI/Bilqis-MLX/commit/d183d617f295df7419c0564970d6412665bd97c3) `test(bamf): specify two-node local package staging (#526)`
- [`990eeadbb5d0`](https://github.com/Entif-AI/Bilqis-MLX/commit/990eeadbb5d0e05ab1192bb6be0eda00faed24ec) `feat(bamf): exchange immutable packages through local staging directories (#526)`
- [`1ea55f40e85d`](https://github.com/Entif-AI/Bilqis-MLX/commit/1ea55f40e85d165badd7a00cd506eaafd6cc8a66) `test(bamf): cover completed publication after directory flush failure (#526)`
- [`37d05e4ed906`](https://github.com/Entif-AI/Bilqis-MLX/commit/37d05e4ed9064a92f3beb29e4928700d18cccc22) `docs(bamf): record local exchange proof and independent review (#526)`
- [`6116aee01f6c`](https://github.com/Entif-AI/Bilqis-MLX/commit/6116aee01f6c5b5935c8c55c3ae06fb5c3d57c09) `docs(bamf): ratify A09.4 deterministic projection authority`
- [`94cb1d58b9dd`](https://github.com/Entif-AI/Bilqis-MLX/commit/94cb1d58b9dd845b73cb86af858e67910f6e7989) `test(bamf): complete held preflight immutability and refusal proof (#522)`
- [`65cd29affacc`](https://github.com/Entif-AI/Bilqis-MLX/commit/65cd29affaccf83f9d2b0b07625d6e3496d01576) `docs(bamf): record independent recursive census review (#347)`
- [`f40953b7c0c0`](https://github.com/Entif-AI/Bilqis-MLX/commit/f40953b7c0c04c6591eeb68952d52a6be104b240) `chore(bamf): consume reviewed census for lossless registry reconciliation (#347)`
- [`4aa33b304d8d`](https://github.com/Entif-AI/Bilqis-MLX/commit/4aa33b304d8d7022841c65a4c86654203ad5f200) `test(bamf): pin lossless child dependency evidence and held readiness (#347)`
- [`ff6e957fb4f1`](https://github.com/Entif-AI/Bilqis-MLX/commit/ff6e957fb4f1e8b62af2983bd834d7b663de5dbc) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into feature/bamf-a08-2-419-20261030`
- [`19611c6c353d`](https://github.com/Entif-AI/Bilqis-MLX/commit/19611c6c353d0f367e12ef8248beeea019e3b598) `feat(bamf): validate pinned dependency evidence without runnable credit (#347)`
- [`a9ed4f480a93`](https://github.com/Entif-AI/Bilqis-MLX/commit/a9ed4f480a93e2e401fcf850a602668c1c0bacc8) `feat(bamf): bind stable capability identity to releases (#419)`
- [`695ed8d7a06c`](https://github.com/Entif-AI/Bilqis-MLX/commit/695ed8d7a06c4bf54c4b969fe7aaa7cd112d0f2f) `fix(bamf): source stable family authority from release binding (#419)`
- [`c70040d6845b`](https://github.com/Entif-AI/Bilqis-MLX/commit/c70040d6845becf95420d9b02a8cae79e496a507) `feat(bamf): register late child packets with explicit dependency holds (#347)`
- [`9e1f6fa0866b`](https://github.com/Entif-AI/Bilqis-MLX/commit/9e1f6fa0866bbde3bfae548db47f5c7bc45fb9df) `chore(bamf): canonicalize identity binding error (#419)`
- [`9b3dbe212b00`](https://github.com/Entif-AI/Bilqis-MLX/commit/9b3dbe212b009a5b020423cc599f6275da36b0c1) `fix(bamf): retain dependency holds when entry evidence is removed (#347)`
- [`d2ec0645b685`](https://github.com/Entif-AI/Bilqis-MLX/commit/d2ec0645b6852a82b352d1c9b7585106bfff696a) `docs(bamf): record registry review and precise parser guarantee (#347)`
- [`7507d59ebb86`](https://github.com/Entif-AI/Bilqis-MLX/commit/7507d59ebb86b3393e0ef280893a98d0445902b3) `refactor(bamf): give source clause formats a cohesive owner (#347)`
- [`ba053e45a44a`](https://github.com/Entif-AI/Bilqis-MLX/commit/ba053e45a44ae82599483de8c518775397dcd54e) `test(bamf): specify explicit producer and parent amendment syntax (#347)`
- [`513bbd9b6bfc`](https://github.com/Entif-AI/Bilqis-MLX/commit/513bbd9b6bfcd7231f5935e2aaf15f6e1b87c918) `feat(bamf): normalize explicit producer and parent prerequisites (#347)`
- [`f05831af13fa`](https://github.com/Entif-AI/Bilqis-MLX/commit/f05831af13fa12cfdad97d76479e653616b40da3) `refactor(bamf): compartmentalize atlas frontier`
- [`f8b731e08aab`](https://github.com/Entif-AI/Bilqis-MLX/commit/f8b731e08aab72b9c3a0c8c5811f19faca8bd922) `docs(bamf): record explicit format review and remaining holds (#347)`
- [`1387fa1462b1`](https://github.com/Entif-AI/Bilqis-MLX/commit/1387fa1462b130cceb4d48d30dc777a4c93d5527) `fix(bamf): rederive stable capability authority`
- [`e928d6e12dac`](https://github.com/Entif-AI/Bilqis-MLX/commit/e928d6e12dacaf56814cf04afd92d002711865b8) `fix(bamf): distinguish stable operator identities`
- [`62f37c658465`](https://github.com/Entif-AI/Bilqis-MLX/commit/62f37c658465c635ed0ac2d111dd853bb45b0d53) `fix(bamf): bind capability identity to source authority`
- [`a5d44f2c08c0`](https://github.com/Entif-AI/Bilqis-MLX/commit/a5d44f2c08c0f6b3dd52b284e8c99dc12b9cb621) `fix(bamf): reject formal teaching-root drift`
- [`29fff323d91f`](https://github.com/Entif-AI/Bilqis-MLX/commit/29fff323d91ff9334c13eb0fde18a7c655a22caa) `fix(bamf): replay capability source authority`
- [`77a05ef00337`](https://github.com/Entif-AI/Bilqis-MLX/commit/77a05ef00337e8a3773d070adad4c8874c9c1034) `feat(bamf): bind stable capability identity to Factory releases (BAMF A08.2)`
- [`ba8a4f6f9f39`](https://github.com/Entif-AI/Bilqis-MLX/commit/ba8a4f6f9f398c54515ddd69825af03e5f89ab5d) `fix(bamf): rederive frontier projection authority`
- [`21b978ad84d4`](https://github.com/Entif-AI/Bilqis-MLX/commit/21b978ad84d4942b24fe800416c856ba20fac0b3) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into feat/bamf-a09-4-394-final-20261101`
- [`bfd39cfac023`](https://github.com/Entif-AI/Bilqis-MLX/commit/bfd39cfac023674c2d755a477209bdcebcbed013) `test(bamf): keep projection authority fixture immutable`
- [`d42152994b2b`](https://github.com/Entif-AI/Bilqis-MLX/commit/d42152994b2bde4e5be07a956d7f6cb2e4271f9a) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/b11-586-refresh-20261101`
- [`4e9ff317b503`](https://github.com/Entif-AI/Bilqis-MLX/commit/4e9ff317b503747ac142e41eb6787f2bec371d51) `fix(bamf): prove real projection authority path`
- [`76383e474245`](https://github.com/Entif-AI/Bilqis-MLX/commit/76383e474245bf9a61acc278ff84decc177a6c97) `fix(bamf): rederive B11 receipt authority`
- [`793882f1d942`](https://github.com/Entif-AI/Bilqis-MLX/commit/793882f1d942b8212faacdfbfa52625bfd0400c1) `fix(bamf): bind projection and receipt authority`
- [`6a0257383a4e`](https://github.com/Entif-AI/Bilqis-MLX/commit/6a0257383a4ec8a19665b518b33925b03944fe28) `fix(bamf): close projection authority review gaps`
- [`0cac1a27abfb`](https://github.com/Entif-AI/Bilqis-MLX/commit/0cac1a27abfb909b61646e5303ed40e9f60aa977) `Merge pull request #683 from Entif-AI/feat/bamf-a09-4-394-final-20261101`
- [`ab9c035f4673`](https://github.com/Entif-AI/Bilqis-MLX/commit/ab9c035f46734a46b78494640cfaeab5d42a603a) `fix(bamf): restore admission proof fixture imports`
- [`f3ad98745cef`](https://github.com/Entif-AI/Bilqis-MLX/commit/f3ad98745cef78df87b60d39af4fc2adbb0a5787) `Merge pull request #668 from Entif-AI/codex/bamf02-c12-525-manifest-20261101`
- [`29fcb430129f`](https://github.com/Entif-AI/Bilqis-MLX/commit/29fcb430129fa835890e71a8628749c2797591d3) `Merge pull request #669 from Entif-AI/codex/bamf02-c11-524-provenance-20261101`
- [`1b5748afa13e`](https://github.com/Entif-AI/Bilqis-MLX/commit/1b5748afa13e2db099fd67ef2ca7e15fc5dc9b18) `Merge pull request #678 from Entif-AI/codex/bamf02-c11-522-qualify-20261101`
- [`a6d8a000655f`](https://github.com/Entif-AI/Bilqis-MLX/commit/a6d8a000655f4f1e20d9ca2b100dafebd321cda5) `Merge pull request #682 from Entif-AI/codex/bamf02-c01-347-registry-20261101`
- [`97c9c5496405`](https://github.com/Entif-AI/Bilqis-MLX/commit/97c9c54964059e72103eff7e7907d6d83f6ab11c) `Merge pull request #687 from Entif-AI/codex/bamf02-c-685-admission-fixtures-20261101`
- [`045633f55be3`](https://github.com/Entif-AI/Bilqis-MLX/commit/045633f55be3f8c80958c971d3c610cd1382cf0a) `fix(bamf): load cognitive package tests through canonical fixtures`
- [`7fc6632f9b4e`](https://github.com/Entif-AI/Bilqis-MLX/commit/7fc6632f9b4e7adc83ae5a57e995bc75aff61302) `feat(bamf): qualify B07 motifs from source owners`
- [`bd62f3cb6c29`](https://github.com/Entif-AI/Bilqis-MLX/commit/bd62f3cb6c296151aba7b9ed5fa90ee814492494) `fix(bamf): restore cognitive package file-runner compatibility`
- [`11835419c9af`](https://github.com/Entif-AI/Bilqis-MLX/commit/11835419c9af14ff4f0b6768ac81bb4633dcc548) `fix(bamf): keep B07 source-family map immutable`
- [`3fc29876ca32`](https://github.com/Entif-AI/Bilqis-MLX/commit/3fc29876ca32065bc92f36e3419fda7ba3a8dd36) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/b07-456-source-bridge-20261101`
- [`b1c9c8137c3a`](https://github.com/Entif-AI/Bilqis-MLX/commit/b1c9c8137c3a18be5a4f0cf51a9cdbeb1c947aa6) `fix(bamf): close B07 source authority bypasses`
- [`5aae3a86a765`](https://github.com/Entif-AI/Bilqis-MLX/commit/5aae3a86a76577fdde933b6123064a13fb1e5712) `fix(bamf): fail closed on unauthenticated motif history`
- [`3e9557dcd714`](https://github.com/Entif-AI/Bilqis-MLX/commit/3e9557dcd714b413804dd0b732c3a92e34c56a19) `feat(bamf): derive per-step plasticity masks`
- [`0633663d2aed`](https://github.com/Entif-AI/Bilqis-MLX/commit/0633663d2aed2c2ee34b9b2ee9cd7b9319f67959) `test(bamf): clean participation fixture formatting`
- [`d63c46aa5e6b`](https://github.com/Entif-AI/Bilqis-MLX/commit/d63c46aa5e6b66d73e5c15854e340529cefc25d2) `fix(bamf): compose formal source types without retyping A06`
- [`bf9b1262b035`](https://github.com/Entif-AI/Bilqis-MLX/commit/bf9b1262b035cb78f8bc2d6ff54f3d5b6bb14bdd) `fix(bamf): rederive formal types from pinned schema authority`
- [`b4bc1cafb149`](https://github.com/Entif-AI/Bilqis-MLX/commit/b4bc1cafb149c1e5a24d7a28da85dccef032e978) `fix(bamf): bind formal types to source identity`
- [`091010039add`](https://github.com/Entif-AI/Bilqis-MLX/commit/091010039add9740cd824654ad50980a234cf55f) `fix(bamf): carry B09 mask authority into AdamW`
- [`19c1f334b793`](https://github.com/Entif-AI/Bilqis-MLX/commit/19c1f334b7930485a81d78e13ab886dea18d797b) `fix(bamf): issue B09 optimizer masks from derived authority`
- [`2e29b94553c4`](https://github.com/Entif-AI/Bilqis-MLX/commit/2e29b94553c4a059c523aa80ef348b16828eabe3) `fix(bamf): keep B09 masks data not credentials`
- [`46c2edaeffa1`](https://github.com/Entif-AI/Bilqis-MLX/commit/46c2edaeffa1e6769a246dbed6ba8696c8973048) `refactor(bamf): split causal compiler and mirrored witnesses (#347)`
- [`11b2b736723d`](https://github.com/Entif-AI/Bilqis-MLX/commit/11b2b736723d791216c6f54964fae5e5967724b8) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/bamf02-c01-347-registry-20261101`
- [`d22143d395d4`](https://github.com/Entif-AI/Bilqis-MLX/commit/d22143d395d44e4d73300f5228d8dc7bc48a8536) `docs(bamf): record compiler integration proof (#347)`
- [`36a20a83d32e`](https://github.com/Entif-AI/Bilqis-MLX/commit/36a20a83d32ecebe57a99962bda41dc3560009e3) `fix(bamf): keep local-slot participation row-scoped`
- [`f683f9f9d1fe`](https://github.com/Entif-AI/Bilqis-MLX/commit/f683f9f9d1fe14916f31cca2660a46d15bbe110e) `refactor(bamf): split partial forest authority and receipts (#347)`
- [`95b788d7605c`](https://github.com/Entif-AI/Bilqis-MLX/commit/95b788d7605c282b00e5cb86acdecd0959cd534f) `docs(bamf): record partial forest native proof (#347)`
- [`ff2fc3d6a67b`](https://github.com/Entif-AI/Bilqis-MLX/commit/ff2fc3d6a67ba241ead7071c38ad8372e779ba94) `refactor(bamf): split released schema artifacts and source pins (#347)`
- [`278c49dd190f`](https://github.com/Entif-AI/Bilqis-MLX/commit/278c49dd190f19083e06017aab18930c92f1d855) `docs(bamf): record released schema native proof (#347)`
- [`e6a94f111588`](https://github.com/Entif-AI/Bilqis-MLX/commit/e6a94f111588d4fb7ad9be53d8d61fcbd2b9c06e) `refactor(bamf): split frame schema records and source authority (#347)`
- [`938108c34b1c`](https://github.com/Entif-AI/Bilqis-MLX/commit/938108c34b1cbe3beda4fe54363dedd7e2e1c7a4) `docs(bamf): record frame schema native proof (#347)`
- [`4ab0752d9bda`](https://github.com/Entif-AI/Bilqis-MLX/commit/4ab0752d9bdafeee25c486bb0ef5979872d48281) `refactor(bamf): split frame codec and mirrored witnesses (#347)`
- [`cb5da461d6c3`](https://github.com/Entif-AI/Bilqis-MLX/commit/cb5da461d6c35672001bd061040260ac7f9a5f21) `docs(bamf): record native and installed interface proof (#347)`
- [`4405d1eb11f9`](https://github.com/Entif-AI/Bilqis-MLX/commit/4405d1eb11f90e15cc7685bbbedebea955dd283e) `refactor(semantics): split frame codec owners`
- [`968ba4cb718b`](https://github.com/Entif-AI/Bilqis-MLX/commit/968ba4cb718bdf0ff06d0d2f4b79678886ba297a) `fix(semantics): verify frame types at readout`
- [`888c039835ca`](https://github.com/Entif-AI/Bilqis-MLX/commit/888c039835ca321fd363d510b2812ce042a3b4b0) `fix(semantics): fail closed without frame type authority`
- [`ad78eabe6d1f`](https://github.com/Entif-AI/Bilqis-MLX/commit/ad78eabe6d1fbb947b55261abef4f77bf55ef6b6) `fix(semantics): preserve frame codec public identity`
- [`76c1c03ad67b`](https://github.com/Entif-AI/Bilqis-MLX/commit/76c1c03ad67b25d76fedc4db25c87be078350733) `fix(bamf): preserve A04 frame type and codec identity`
- [`4a51589bfc22`](https://github.com/Entif-AI/Bilqis-MLX/commit/4a51589bfc227f67125f183e1aa730ea77e39d0c) `refactor(source): split school adapter ownership`
- [`bd0e60fec629`](https://github.com/Entif-AI/Bilqis-MLX/commit/bd0e60fec62920cd6bd69eb694f56ca98fda8fbe) `style(source): normalize extracted owner whitespace`
- [`157ef5e12a39`](https://github.com/Entif-AI/Bilqis-MLX/commit/157ef5e12a391da51a1fa93ac1b07967eb48758e) `test(registry): rule registry, 420, roobie doobie doo`
- [`9e73a8139074`](https://github.com/Entif-AI/Bilqis-MLX/commit/9e73a81390745d85fce19b50288649a67169309e) `feat(factory): register source-qualified world rules`
- [`e552963a5eef`](https://github.com/Entif-AI/Bilqis-MLX/commit/e552963a5eefda702de6c9c9484d968223c82ece) `fix(runtime): bind training source lineage`
- [`aed44c42c401`](https://github.com/Entif-AI/Bilqis-MLX/commit/aed44c42c401d383b2b579077fba51e02bef65bf) `fix(factory): harden qualified world dispatch`
- [`d2e10f04a4b8`](https://github.com/Entif-AI/Bilqis-MLX/commit/d2e10f04a4b8e9b0c2e22504c8aa58c47d7989fe) `fix(factory): preserve source oracle boundary`
- [`3088ee02d085`](https://github.com/Entif-AI/Bilqis-MLX/commit/3088ee02d085f2a88e53b7c78c8d9637916663fe) `docs: add BAMF-0.2 architecture blueprint`
- [`053a632d32fd`](https://github.com/Entif-AI/Bilqis-MLX/commit/053a632d32fde375f67027140fee3745db17315a) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/b09-465-participation-20261101`
- [`7bebebf342e5`](https://github.com/Entif-AI/Bilqis-MLX/commit/7bebebf342e540f5bcd757163b9a1ec881e336f9) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/bamf02-b14-4-485-refresh-20261101`
- [`bdd26c2e9a99`](https://github.com/Entif-AI/Bilqis-MLX/commit/bdd26c2e9a995066573a7fdb459fb85e25ed0380) `fix(bamf): freeze B09 identity admission at candidate start`
- [`d2e2c1e217bc`](https://github.com/Entif-AI/Bilqis-MLX/commit/d2e2c1e217bc8f1ef08b9a4c05b77b83e224d33f) `merge: refresh #526 exchange onto reviewed unified`
- [`8b08483d0c02`](https://github.com/Entif-AI/Bilqis-MLX/commit/8b08483d0c02db955d4f4a854bf27c25a313cecd) `fix(bamf): bind cache payload to rights authority`
- [`24df847fac51`](https://github.com/Entif-AI/Bilqis-MLX/commit/24df847fac51fe3056d16fcb22b1438f4fb7cae6) `test(bamf): refresh cognitive package fixture import`
- [`c0e791acc910`](https://github.com/Entif-AI/Bilqis-MLX/commit/c0e791acc910cb1f3d64d285abfa963822dbe8c5) `fix(bamf): authenticate cache artifacts under pinned authority`
- [`bfada2678ad6`](https://github.com/Entif-AI/Bilqis-MLX/commit/bfada2678ad6bd44ae7a297d101b96ac8292fbea) `fix(bamf): name cache signature width contract`
- [`1fa61a010ae5`](https://github.com/Entif-AI/Bilqis-MLX/commit/1fa61a010ae5b16eca4a28952348e9f77b6bb3c9) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/691-formal-type-composition-20261101`
- [`d85377cbfa95`](https://github.com/Entif-AI/Bilqis-MLX/commit/d85377cbfa957ad8f6cac4c36cc3fdb2eba8e018) `refactor(compatibility): split historical release and recovery owners`
- [`91329398a823`](https://github.com/Entif-AI/Bilqis-MLX/commit/91329398a8235a3479f3fdcc5a1427bd2441bcb4) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/b07-456-source-bridge-20261101`
- [`e3e010c21196`](https://github.com/Entif-AI/Bilqis-MLX/commit/e3e010c2119660becc49473d3c5e34ecbccafbd3) `refactor(tests): split live profile execution fixtures`
- [`3af3e3d8f06d`](https://github.com/Entif-AI/Bilqis-MLX/commit/3af3e3d8f06ddd04179426b1feb92daf9ac3998a) `feat(bamf): stage retained plastic delta candidates`
- [`92bdff370e9b`](https://github.com/Entif-AI/Bilqis-MLX/commit/92bdff370e9be3d0c64eb4ffe300d2448f53d6a1) `feat(bamf): compose source-qualified formal types without retyping A06 (B02)`
- [`9ef240ccc8ba`](https://github.com/Entif-AI/Bilqis-MLX/commit/9ef240ccc8ba2f0c3d1bafa95d32091bb1b8b9ef) `fix(bamf): seal disposable delta custody`
- [`41e37cf60a93`](https://github.com/Entif-AI/Bilqis-MLX/commit/41e37cf60a934181548e9b343ddab1ce2b3849a7) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/bamf02-c12-526-exchange-20261101`
- [`a1025e442277`](https://github.com/Entif-AI/Bilqis-MLX/commit/a1025e442277ee71b2120f87b9254179cee88dfb) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/b09-465-participation-20261101`
- [`547471d2b95f`](https://github.com/Entif-AI/Bilqis-MLX/commit/547471d2b95fadbbd7fa3631db0d0a56a20436c9) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/b07-456-source-bridge-20261101`
- [`f3e99245c49f`](https://github.com/Entif-AI/Bilqis-MLX/commit/f3e99245c49f7df897d71cdcc7dfc69710014c65) `refactor(runtime): split checkpoint custody and preserve error inventory`
- [`589d3c6c9a21`](https://github.com/Entif-AI/Bilqis-MLX/commit/589d3c6c9a215da30a11581610dddd832fe41d6c) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/bamf02-c11-524-preflight-runbook-20261101`
- [`fb86c2f72a30`](https://github.com/Entif-AI/Bilqis-MLX/commit/fb86c2f72a302ec786f6cbf94dd4f1daedd9e73f) `fix(runtime): bind source AST semantics to frame evidence`
- [`28c02196f2b0`](https://github.com/Entif-AI/Bilqis-MLX/commit/28c02196f2b06e05981c66bf788ea0acf08f2dff) `chore(bamf): add flow-control policy.json`
- [`774e17bcf4b0`](https://github.com/Entif-AI/Bilqis-MLX/commit/774e17bcf4b09a5ec5aa540737a4a803ca93c0c8) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into fix/bamf-c02-1-source-lineage-20261101`
- [`b552b276e8dd`](https://github.com/Entif-AI/Bilqis-MLX/commit/b552b276e8dd71ff411afd18c9e06f53cc9b7d38) `chore(bamf): add flow-control lane-a.json`
- [`2c85cb1cc0b3`](https://github.com/Entif-AI/Bilqis-MLX/commit/2c85cb1cc0b3a78ad1fa482565ff3d69c558c454) `chore(bamf): add flow-control lane-b.json`
- [`d98d7292d1a6`](https://github.com/Entif-AI/Bilqis-MLX/commit/d98d7292d1a604e71f87b810dbb67fe77ccae46e) `chore(bamf): add flow-control lane-c.json`
- [`e7dbeb980383`](https://github.com/Entif-AI/Bilqis-MLX/commit/e7dbeb980383ec3955c40a0bfe2ee95a6190b273) `chore(bamf): add flow-control check_bamf_flow_control.py`
- [`228e3f337d86`](https://github.com/Entif-AI/Bilqis-MLX/commit/228e3f337d868e826a6046b86225c56d6ff7afe2) `chore(bamf): add flow-control test_bamf_flow_control.py`
- [`1bba23443858`](https://github.com/Entif-AI/Bilqis-MLX/commit/1bba234438586219747d99453552d214d183cacc) `docs(bamf): codify parked-PR flow control`
- [`1e25e8c9ffd9`](https://github.com/Entif-AI/Bilqis-MLX/commit/1e25e8c9ffd9db8ad79750c5a27952eb0368f2e8) `docs(bamf): add execution flow-control contract`
- [`8333d69d34d7`](https://github.com/Entif-AI/Bilqis-MLX/commit/8333d69d34d74eb57c0345e69b573485947184ad) `docs(bamf): socialize Lane A WIP preflight`
- [`40a6db340300`](https://github.com/Entif-AI/Bilqis-MLX/commit/40a6db340300f09c2f40bb95fe144847cb128d10) `docs(bamf): socialize Lane B WIP preflight`
- [`d1f0b464737e`](https://github.com/Entif-AI/Bilqis-MLX/commit/d1f0b464737eef5e3263c0f4aa9d280802ed44a4) `docs(bamf): socialize Lane C WIP preflight`
- [`5753544241a6`](https://github.com/Entif-AI/Bilqis-MLX/commit/5753544241a6385b8c33395da40b6c464c21a673) `build(bamf): enforce flow-control in quality checks`
- [`392c80b3afc3`](https://github.com/Entif-AI/Bilqis-MLX/commit/392c80b3afc332d69a2f89c8778ca9286bcf818b) `docs(adr): accept BAMF parked-PR flow control`
- [`8b6b482e2329`](https://github.com/Entif-AI/Bilqis-MLX/commit/8b6b482e2329e56d636659c83166fd025a96e1db) `docs(bamf): scope flow state to lane-owned PRs`
- [`91add48e2e56`](https://github.com/Entif-AI/Bilqis-MLX/commit/91add48e2e568fe09f6ff8e216b05aa56e45e149) `docs(adr): clarify lane-owned flow-control scope`
- [`a9bfeab82c28`](https://github.com/Entif-AI/Bilqis-MLX/commit/a9bfeab82c281b603f3867b1058295ccd5a7b492) `test(bamf): run flow-control regressions in quality gates`
- [`9dfe0e303fa6`](https://github.com/Entif-AI/Bilqis-MLX/commit/9dfe0e303fa63b3a28f2d74b7347229f9ba9ab98) `refactor(bamf): simplify flow-control validation`
- [`533d171dc70f`](https://github.com/Entif-AI/Bilqis-MLX/commit/533d171dc70fa99f084e74e4021403ebec5a149a) `test(bamf): keep flow-control fixtures immutable by construction`
- [`3bd9fb696dcb`](https://github.com/Entif-AI/Bilqis-MLX/commit/3bd9fb696dcb822a15f12a72d8c5f25345b679f2) `fix(bamf): repair flow-control test fixture module`
- [`16fc98437ee3`](https://github.com/Entif-AI/Bilqis-MLX/commit/16fc98437ee32cccae1a79f168fcd031a5c99ca8) `ci(bamf): enforce lane flow-control state`
- [`07ec2646ccc3`](https://github.com/Entif-AI/Bilqis-MLX/commit/07ec2646ccc320e5f781d85b003541332331a5ab) `fix(runtime): reject unsafe BAMF run roots`
- [`195fc65a2f86`](https://github.com/Entif-AI/Bilqis-MLX/commit/195fc65a2f867f99ad12ea097d66fad1726a7053) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/bamf02-b13-478-custody-20261101`
- [`fe912417d484`](https://github.com/Entif-AI/Bilqis-MLX/commit/fe912417d484d46bbd9b283593c3bbe76e4b0351) `feat(bamf): enforce parked-PR flow control and lane WIP limits`
- [`d0f94e99ff9d`](https://github.com/Entif-AI/Bilqis-MLX/commit/d0f94e99ff9d1a41838dd364b2bdec6e3d079341) `chore(bamf): activate C02.1 review repair (#490)`
- [`9facb1dd528e`](https://github.com/Entif-AI/Bilqis-MLX/commit/9facb1dd528ee4861ff02701d6df5efb876a7000) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/bamf490-review-repair-20261102`
- [`d1b4860389e3`](https://github.com/Entif-AI/Bilqis-MLX/commit/d1b4860389e35950e643bffbdec0e2febb1b7506) `fix(bamf): bind C02.1 semantic owners (#490)`
- [`a177a7ff8ee3`](https://github.com/Entif-AI/Bilqis-MLX/commit/a177a7ff8ee3eaeb08c1f34a8baef79b597844da) `docs(agents): protect context from repository census dumps`
- [`323d9db4dbe9`](https://github.com/Entif-AI/Bilqis-MLX/commit/323d9db4dbe924425fa1fd3a4b7585c75d832197) `docs(agents): separate context guard section`
- [`7031cf059453`](https://github.com/Entif-AI/Bilqis-MLX/commit/7031cf0594537414d99418033f6f190a0f598776) `fix(factory): close world family authority seams`
- [`e11121cef847`](https://github.com/Entif-AI/Bilqis-MLX/commit/e11121cef84742dc96b0d4c977dd7cd4cd66a563) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into feat/bamf-a08-3-420-20261101`
- [`ed5df098fddf`](https://github.com/Entif-AI/Bilqis-MLX/commit/ed5df098fddf0e88ccd028652b44ba81e0b235a5) `feat(bamf): keep repository census output out of routine context`
- [`009cb5d9d719`](https://github.com/Entif-AI/Bilqis-MLX/commit/009cb5d9d71905b30ab9f1efc4c6ff8b968003f2) `fix(factory): bind world execution to canonical authority`
- [`be9426937428`](https://github.com/Entif-AI/Bilqis-MLX/commit/be9426937428e77237af42b2ad019635046ec6e5) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into feat/bamf-a08-3-420-20261101`
- [`0d43c1be0900`](https://github.com/Entif-AI/Bilqis-MLX/commit/0d43c1be09002c6063a5605008eac0339b923011) `test(factory): freeze world identity fixtures`
- [`421ee5eeee21`](https://github.com/Entif-AI/Bilqis-MLX/commit/421ee5eeee21461f8355ffbde8aeb1409e5cb632) `fix(factory): namespace source world query operators`
- [`2c80599dfac0`](https://github.com/Entif-AI/Bilqis-MLX/commit/2c80599dfac07f3e5eaf5d82adf74411dc21b826) `fix(errors): structure BAMF world rule failures`
- [`50ebc8caeb05`](https://github.com/Entif-AI/Bilqis-MLX/commit/50ebc8caeb050bd811d85e769c0fbab649259174) `Merge commit 'ed5df098fddf0e88ccd028652b44ba81e0b235a5' into cos/worktrees/7c154ddc840c41f2a68d19c0f94ec360/worker-2`
- [`7abd997fab23`](https://github.com/Entif-AI/Bilqis-MLX/commit/7abd997fab23058a52caff870e352bced9646b5e) `refactor(bamf): split revalidation owner modules`
- [`d083671db504`](https://github.com/Entif-AI/Bilqis-MLX/commit/d083671db5042199d5dc6839212f9546a9b72c4d) `fix(bamf): anchor cache signatures to trusted authority`
- [`9616d25a222f`](https://github.com/Entif-AI/Bilqis-MLX/commit/9616d25a222f23c401a5dc9ff2f94e9b21d6cfca) `docs(bamf): activate lane B cache trust repair`
- [`26087f3ae090`](https://github.com/Entif-AI/Bilqis-MLX/commit/26087f3ae0905245b48af36380f8c2dcf9f54efd) `docs(bamf): park reviewed lane B dependency`
- [`6a8a7d75c078`](https://github.com/Entif-AI/Bilqis-MLX/commit/6a8a7d75c078398c6d71d7715a5806aaf3e9a530) `fix(bamf): make B13 bundle publication durable and serialized`
- [`8c93853d4549`](https://github.com/Entif-AI/Bilqis-MLX/commit/8c93853d4549dd65343a81d211b339e7f50c052f) `fix(bamf): own cache authority at host boundary`
- [`18511b9f138d`](https://github.com/Entif-AI/Bilqis-MLX/commit/18511b9f138d0ff765d415e85551b4834db1604b) `docs(bamf): record cache authority repair`
- [`9800132e0492`](https://github.com/Entif-AI/Bilqis-MLX/commit/9800132e0492b000369da368607ccb35b8c5b611) `fix(bamf): leave cache authority upstream-owned`
- [`40158a6b28bd`](https://github.com/Entif-AI/Bilqis-MLX/commit/40158a6b28bd6f65756366c2735692f811390eb0) `docs(bamf): park cache authority on upstream owner`
- [`630f39e186d6`](https://github.com/Entif-AI/Bilqis-MLX/commit/630f39e186d6aac042edf70c63810c9300489732) `fix(runtime): harden B13 custody evidence`
- [`2e65a6fc4147`](https://github.com/Entif-AI/Bilqis-MLX/commit/2e65a6fc414721f24badbead776c7233aeafa317) `docs(bamf): reserve EGM for merge readiness`
- [`bc5e5f7865ee`](https://github.com/Entif-AI/Bilqis-MLX/commit/bc5e5f7865ee190af58ac1ac137053ae3c2dd48a) `fix(runtime): close B13 custody review gaps`
- [`b4f2f0aca316`](https://github.com/Entif-AI/Bilqis-MLX/commit/b4f2f0aca31623e7246ef819338a1450d71183cd) `feat(bamf): reserve fresh EGM review for merge readiness`
- [`58a57cd6a762`](https://github.com/Entif-AI/Bilqis-MLX/commit/58a57cd6a762477424e591afaecd4cf8e25ef89b) `fix(runtime): satisfy B13 error-control contract`
- [`c7bab0b5cb50`](https://github.com/Entif-AI/Bilqis-MLX/commit/c7bab0b5cb5065eb5bbb2a6b241ba85a533407e5) `fix(runtime): validate complete B13 bundle custody`
- [`18a8b857874f`](https://github.com/Entif-AI/Bilqis-MLX/commit/18a8b857874fe55df7089f283cf9fc531c31e14b) `merge: consume current BAMF unified before B13 turn-in`
- [`4aa40c427cda`](https://github.com/Entif-AI/Bilqis-MLX/commit/4aa40c427cda2ac2f0bac85c6e46e4b0724b2c22) `test(runtime): lock exact B13 custody spelling`
- [`5ac0e9ca2a94`](https://github.com/Entif-AI/Bilqis-MLX/commit/5ac0e9ca2a94e11a6bbb25bcca8282af3eb8fc4e) `fix(bamf): close B13 custody EGM defects (#478)`
- [`00d78c1f37e0`](https://github.com/Entif-AI/Bilqis-MLX/commit/00d78c1f37e0076c4c29fce0a7c3b8edc93d44d1) `Merge commit '5ac0e9ca2a94e11a6bbb25bcca8282af3eb8fc4e' into codex/remediation-712-20261102`
- [`830486121aaa`](https://github.com/Entif-AI/Bilqis-MLX/commit/830486121aaaa84e819fe38e882ebdd86a373b0a) `Merge commit '5ac0e9ca2a94e11a6bbb25bcca8282af3eb8fc4e' into codex/713-canonical-model-input-20261102`
- [`39b64a8fd424`](https://github.com/Entif-AI/Bilqis-MLX/commit/39b64a8fd42407e65b21bfcae0dc5f19c8e9d00a) `Merge commit '5ac0e9ca2a94e11a6bbb25bcca8282af3eb8fc4e' into codex/cache-authority-719-720-20261102`
- [`fc4a11e019af`](https://github.com/Entif-AI/Bilqis-MLX/commit/fc4a11e019af69fb98c04310771211f4b100d216) `chore(bamf): activate requested authority remediations`
- [`fe854477c41a`](https://github.com/Entif-AI/Bilqis-MLX/commit/fe854477c41a841f097e5060f6a167314b886899) `fix(runtime): converge checkpoint facade custody hooks`
- [`7dafcfb8a657`](https://github.com/Entif-AI/Bilqis-MLX/commit/7dafcfb8a6575826c8dc8744c03e1bcd93d516d6) `fix(cache): reject unissued authority capabilities`
- [`563596e936b6`](https://github.com/Entif-AI/Bilqis-MLX/commit/563596e936b660c384a0b6f93b4f88081627575a) `fix(bamf): carry source selection into depth composition`
- [`a5232e1240e4`](https://github.com/Entif-AI/Bilqis-MLX/commit/a5232e1240e47cb8d5910e67821b9742e9e5ea3e) `fix(runtime): consume unified checkpoint custody and restore facade injection`
- [`168d7976999a`](https://github.com/Entif-AI/Bilqis-MLX/commit/168d7976999a0f9eccdd47a0877f19c6a11aff7d) `docs(c11): correct checkpoint review and record crash replay proof`
- [`3f7846eb4d2f`](https://github.com/Entif-AI/Bilqis-MLX/commit/3f7846eb4d2f68b880a247ffdc8572171ddb486e) `docs(agents): close completed remediation artifacts`
- [`c0527cb7a56d`](https://github.com/Entif-AI/Bilqis-MLX/commit/c0527cb7a56db23e20828148b7cde721a8757e1f) `docs(bamf): make EGM findings ephemeral remediation work`
- [`17bd671ede0b`](https://github.com/Entif-AI/Bilqis-MLX/commit/17bd671ede0bddc0982e0fa5c921fbc3677908b7) `docs(adr): close remediation artifacts at local acceptance`
- [`247c3f273c90`](https://github.com/Entif-AI/Bilqis-MLX/commit/247c3f273c90a655a0c6b4700a87c1942254078c) `docs(agents): avoid unnecessary remediation PRs`
- [`30a5bd659839`](https://github.com/Entif-AI/Bilqis-MLX/commit/30a5bd659839e7f7a64c32a80259df157e449ebf) `docs(bamf): avoid archival remediation PRs`
- [`d024b2c33679`](https://github.com/Entif-AI/Bilqis-MLX/commit/d024b2c33679dbff9a718b63c7fba4e05c8f6a39) `docs(adr): minimize remediation PR proliferation`
- [`212c198d617b`](https://github.com/Entif-AI/Bilqis-MLX/commit/212c198d617bb17b639252f3b8d494a0d9e21941) `Merge commit '5ac0e9ca2a94e11a6bbb25bcca8282af3eb8fc4e' into codex/participation-711-20261102`
- [`65d33d3dcfd8`](https://github.com/Entif-AI/Bilqis-MLX/commit/65d33d3dcfd8cbbbfc12ff19279ade25edf8c0f7) `chore(bamf): select canonical participation validation`
- [`57d7247442cd`](https://github.com/Entif-AI/Bilqis-MLX/commit/57d7247442cd508e8336b1e48c9804b9585995e6) `docs(agents): explicitly close nondefault remediation issues`
- [`634b8eef2d66`](https://github.com/Entif-AI/Bilqis-MLX/commit/634b8eef2d66305889d8278545adcaedea65e380) `docs(bamf): require explicit remediation issue closeout`
- [`de09397e9cf1`](https://github.com/Entif-AI/Bilqis-MLX/commit/de09397e9cf1fa1690f001f8006c18985308b16c) `docs(adr): require explicit nondefault issue closeout`
- [`207a312208d1`](https://github.com/Entif-AI/Bilqis-MLX/commit/207a312208d1a7cd8c2f8c9533c6522fb700c22f) `refactor(runtime): split serialized operator session into cohesive owners`
- [`953d3da898f8`](https://github.com/Entif-AI/Bilqis-MLX/commit/953d3da898f81ee3906ed41ebe239f4fbbfa25c9) `docs(c11): document integrated held configuration inspections`
- [`c4eb468e579f`](https://github.com/Entif-AI/Bilqis-MLX/commit/c4eb468e579fa5f3fee187e663ee5787f92aef05) `fix(plasticity): validate update groups against B01 ledger`
- [`bf1a17cf734c`](https://github.com/Entif-AI/Bilqis-MLX/commit/bf1a17cf734ce88440fbc5a8babdc0cd7fae8623) `refactor(semantics): split causal frame compilation by owner`
- [`3112943b47aa`](https://github.com/Entif-AI/Bilqis-MLX/commit/3112943b47aa665febb6cf299fd45e4384a19312) `refactor(semantics): split released schema authority owners`
- [`290c1d06fe2e`](https://github.com/Entif-AI/Bilqis-MLX/commit/290c1d06fe2ed56a6661713fb2577fdfe8cf4aef) `fix(bamf): rederive model input source authority`
- [`d112021d74df`](https://github.com/Entif-AI/Bilqis-MLX/commit/d112021d74df021b730a670b3cc6a8509cc401f5) `fix(bamf): make formal source rejection unconditional`
- [`e428dbd4c05b`](https://github.com/Entif-AI/Bilqis-MLX/commit/e428dbd4c05bc6503bc40ac6ddcb4e3530b9d131) `fix(semantics): preserve released schema module identity`
- [`7a3db5cfb8b9`](https://github.com/Entif-AI/Bilqis-MLX/commit/7a3db5cfb8b9075b117eadf09c9016540ae30918) `feat(bamf): close remediation artifacts at local acceptance`
- [`3274e7ba753d`](https://github.com/Entif-AI/Bilqis-MLX/commit/3274e7ba753d8ecfc85cfcf3e0de9f9893cb7be6) `refactor(runtime): bound operator functions and verify complete added-file scope`
- [`fe5f4a1380ff`](https://github.com/Entif-AI/Bilqis-MLX/commit/fe5f4a1380ff14dabb98d3b07fb00ffcc4bc442a) `fix(cache): reject unissued authority capabilities`
- [`626b7553de02`](https://github.com/Entif-AI/Bilqis-MLX/commit/626b7553de0231592b486cafd1e012012f580144) `fix(bamf): carry formal source selection into B05`
- [`96cbf751be8b`](https://github.com/Entif-AI/Bilqis-MLX/commit/96cbf751be8b39bdea38c08e1b47336adbcffedd) `Merge branch 'codex/bamf02-c11-524-preflight-runbook-20261101' into codex/729-historical-provider-import-20261102`
- [`5d444befb3e7`](https://github.com/Entif-AI/Bilqis-MLX/commit/5d444befb3e73525b0734ea197e00928962d2ce7) `fix(compatibility): restore historical graph ABI binding`
- [`59ce2940a785`](https://github.com/Entif-AI/Bilqis-MLX/commit/59ce2940a78556162ae63c66cd96b5efd5dc543f) `refactor(bamf): finish operator structure and document held inspections (C11)`
- [`733708a345a7`](https://github.com/Entif-AI/Bilqis-MLX/commit/733708a345a7a3f89fe8b6fae24bd9ce8f4ee1d5) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/716-checkpoint-facade-20261102`
- [`67c964a1548c`](https://github.com/Entif-AI/Bilqis-MLX/commit/67c964a1548cb0075a28a90aa2565d8bdab0fd71) `fix(runtime): preserve checkpoint facade interception`
- [`47eae0193297`](https://github.com/Entif-AI/Bilqis-MLX/commit/47eae0193297fa0fbb0c6cc0bbf46246d284cf38) `chore(bamf): activate C01 after operator turn-in integration`
- [`6ca15979e778`](https://github.com/Entif-AI/Bilqis-MLX/commit/6ca15979e77870c5501b9fe3399f394698cd29fc) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/bamf02-c-runtime`
- [`46bfa98d564e`](https://github.com/Entif-AI/Bilqis-MLX/commit/46bfa98d564e1262be43463ec96d3ce1a95aa8c4) `chore(bamf): record current unified for C01 activation`
- [`bcd2c4c8592f`](https://github.com/Entif-AI/Bilqis-MLX/commit/bcd2c4c8592ff3dea972a82c3db7fd5dfaee82c1) `merge(bamf): consume reviewed codec owners into C01 candidate`
- [`94a4ba57d6e0`](https://github.com/Entif-AI/Bilqis-MLX/commit/94a4ba57d6e0af1282d1ee2ef076b1327521b3e2) `merge: consume completed semantic structural repair`
- [`7c8b75a418e7`](https://github.com/Entif-AI/Bilqis-MLX/commit/7c8b75a418e726060945f2b9cbe296063b7d9ee4) `fix(semantics): resolve canonical codec schema annotations`
- [`cb536f744008`](https://github.com/Entif-AI/Bilqis-MLX/commit/cb536f744008c7e7575c3d3973c135aa38292fd6) `docs(bamf): record refreshed source interface proof and consumed repair`
- [`068eb6bf0ef6`](https://github.com/Entif-AI/Bilqis-MLX/commit/068eb6bf0ef6587df371dff6b7dc7a6f16592b08) `test(bamf): reconcile accepted B05 structural preservation`
- [`6b782ad446dd`](https://github.com/Entif-AI/Bilqis-MLX/commit/6b782ad446dd2307d3f297ebb97448a8c293d40a) `test(bamf): preserve nested definition identities in structural proof`
- [`91b7fedd9ab3`](https://github.com/Entif-AI/Bilqis-MLX/commit/91b7fedd9ab31a89c7ca2586541dee7ab1ae6ae2) `docs(bamf): record structural proof turn-in and accepted dependency`
- [`46ab58913a1d`](https://github.com/Entif-AI/Bilqis-MLX/commit/46ab58913a1df8d3ec95a4d5112512e10955b28d) `docs(bamf): distinguish completed outbox owner from open neural work`
- [`16ba157dcc44`](https://github.com/Entif-AI/Bilqis-MLX/commit/16ba157dcc448640d63386ff011720dca8b9302b) `fix(runtime): preserve public depth factory pickle identity`
- [`aa2aec180925`](https://github.com/Entif-AI/Bilqis-MLX/commit/aa2aec1809256a6270bb8afedc87c2a655175054) `docs(bamf): bind structural turn-in to verified implementation checkpoint`
- [`d67938294331`](https://github.com/Entif-AI/Bilqis-MLX/commit/d67938294331d47687c3220f314d1ddfa7396779) `governance(bamf): bound PR inventory and enforce drain`
- [`318029799ab8`](https://github.com/Entif-AI/Bilqis-MLX/commit/318029799ab8933619d8b13cc3efaa0fd428c621) `fix(bamf): reconcile live PR heads in flow control`
- [`7896f265c9c1`](https://github.com/Entif-AI/Bilqis-MLX/commit/7896f265c9c164806efa1afeb4de93fa3c069efd) `fix(bamf): reconcile live PR heads in flow control`
- [`8758476adba9`](https://github.com/Entif-AI/Bilqis-MLX/commit/8758476adba9d69382334cdce78dfa2e11c97871) `fix(bamf): reconcile live PR heads in flow control`
- [`ce08e26218b4`](https://github.com/Entif-AI/Bilqis-MLX/commit/ce08e26218b4487450bc0c40f5f5ea7e343dc9a1) `refactor(bamf): split flow-control enforcement owners`
- [`b9282cbcd64a`](https://github.com/Entif-AI/Bilqis-MLX/commit/b9282cbcd64ad624e510a5166b7220e0d3176a86) `refactor(bamf): keep inventory gate identity-scoped`
- [`47110550ce43`](https://github.com/Entif-AI/Bilqis-MLX/commit/47110550ce43a6dae932a0260f780ff943067ee1) `refactor(bamf): keep inventory gate identity-scoped`
- [`18f39446be04`](https://github.com/Entif-AI/Bilqis-MLX/commit/18f39446be04190c9f639503b25829697ae1e9b4) `refactor(bamf): keep inventory gate identity-scoped`
- [`8ef2ef88ecfc`](https://github.com/Entif-AI/Bilqis-MLX/commit/8ef2ef88ecfcd0c09e15b99a7ba1267297e4239e) `test(bamf): split flow-control regression owners`
- [`a00b0c7db95b`](https://github.com/Entif-AI/Bilqis-MLX/commit/a00b0c7db95be0aff26dd73543f54a4642ed400e) `test(bamf): keep flow-control fixtures immutable`
- [`8a5871631dfb`](https://github.com/Entif-AI/Bilqis-MLX/commit/8a5871631dfba3c8913931a732f721fda4eb41f5) `test(bamf): keep flow-control fixtures immutable`
- [`3c0cce7c0806`](https://github.com/Entif-AI/Bilqis-MLX/commit/3c0cce7c0806c7d75951d7dbcb98f985efca74a4) `test(bamf): keep flow-control fixtures immutable`
- [`103ba6f46e13`](https://github.com/Entif-AI/Bilqis-MLX/commit/103ba6f46e13ab08e3db97445013be3109168b80) `test(bamf): avoid fixture factory shadowing`
- [`f1d04527fac1`](https://github.com/Entif-AI/Bilqis-MLX/commit/f1d04527fac1a7f63939b1cadf12b28631da2c88) `governance(bamf): pin drain exception to PR 741`
- [`c617d29301f1`](https://github.com/Entif-AI/Bilqis-MLX/commit/c617d29301f15581b93b9f790d5348ee5cb5d3db) `governance(bamf): pin drain exception to PR 741`
- [`8925b67ef353`](https://github.com/Entif-AI/Bilqis-MLX/commit/8925b67ef3538f65a0740cdbc0db702fe0aa5f4b) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/remediation-738-20261102`
- [`be085dfae940`](https://github.com/Entif-AI/Bilqis-MLX/commit/be085dfae94003e5f4b1bfa89b398dcd3962f3db) `governance(bamf): complete initial PR inventory drain`
- [`117f24e25c34`](https://github.com/Entif-AI/Bilqis-MLX/commit/117f24e25c34f5f0739bb04773610c8bf9a7051d) `docs(bamf): record initial inventory drain result`
- [`de5fae7abbdb`](https://github.com/Entif-AI/Bilqis-MLX/commit/de5fae7abbdb41ea342cf893b2ec66658cd0ef1e) `chore(bamf): activate B11 remediation flow`
- [`3769feb1eb83`](https://github.com/Entif-AI/Bilqis-MLX/commit/3769feb1eb836f5de2541deb62982e105c2ec46f) `fix(bamf): preserve EGM drain inventory`
- [`e39128e8bbdf`](https://github.com/Entif-AI/Bilqis-MLX/commit/e39128e8bbdf470f288c70ada9f0b71e02a3876f) `fix(bamf): restore Lane A EGM PR ledger`
- [`8352ad1ca84a`](https://github.com/Entif-AI/Bilqis-MLX/commit/8352ad1ca84af559194fd9f2d7992f52548dc039) `fix(bamf): restore Lane B EGM PR ledger`
- [`f358a7c91e11`](https://github.com/Entif-AI/Bilqis-MLX/commit/f358a7c91e112d561649ffae538cb6d20ac43fe9) `fix(bamf): restore Lane C EGM PR ledger`
- [`1ad8368e84ff`](https://github.com/Entif-AI/Bilqis-MLX/commit/1ad8368e84ff00eebdf943814524a024e1df38f4) `docs(bamf): clarify EGM-first inventory drain`
- [`acec8cc3bd3b`](https://github.com/Entif-AI/Bilqis-MLX/commit/acec8cc3bd3bbac254ede90500e159e798ac119c) `docs(bamf): make EGM-first drain explicit in agent rules`
- [`736d6671973f`](https://github.com/Entif-AI/Bilqis-MLX/commit/736d6671973ffdb3bf3e65d9842c143d371f2aa2) `docs(bamf): clarify EGM-first drain in execution guide`
- [`f78b088bc06b`](https://github.com/Entif-AI/Bilqis-MLX/commit/f78b088bc06b91b73d36016489694210cc57ddf4) `docs(bamf): correct ADR-126 initial drain record`
- [`a14f1fe089d0`](https://github.com/Entif-AI/Bilqis-MLX/commit/a14f1fe089d0105010350468e9733bab387d628a) `refactor(runtime): split visit orchestration phases`
- [`dc9b88b968d1`](https://github.com/Entif-AI/Bilqis-MLX/commit/dc9b88b968d16b5da1c499afa5eb7bd14139a5e2) `docs(bamf): make issue labels canonical EGM queue`
- [`be9f147b55be`](https://github.com/Entif-AI/Bilqis-MLX/commit/be9f147b55be96d685a9d39f8657b05d9df5841e) `refactor(runtime): bound visit phase complexity`
- [`ab21fde414be`](https://github.com/Entif-AI/Bilqis-MLX/commit/ab21fde414be7ab043280558f83d6e1db9077ef7) `fix(bamf): enforce immediate B11 selected boundary (#738)`
- [`44305b1c685f`](https://github.com/Entif-AI/Bilqis-MLX/commit/44305b1c685fcdd43ded307c8eeae8e4e2808fbf) `docs(runtime): refresh visit error ownership`
- [`30d982153927`](https://github.com/Entif-AI/Bilqis-MLX/commit/30d9821539272719eb3361997848189e785de58c) `governance(bamf): reconcile EGM issue-label queue`
- [`6d0f8129df45`](https://github.com/Entif-AI/Bilqis-MLX/commit/6d0f8129df455de6feacdb128266cc273226a08a) `test(bamf): catch tracked stacked PR after parent closure`
- [`3b2290d69011`](https://github.com/Entif-AI/Bilqis-MLX/commit/3b2290d69011fd4a77ffa7619ce8ff76f860c04e) `test(bamf): expose closed-parent stacked PR reconciliation`
- [`f6527112e49d`](https://github.com/Entif-AI/Bilqis-MLX/commit/f6527112e49dffee22f6bb039dd322c554c2487b) `governance(bamf): retain active pending EGM review PR`
- [`7d7172a8369c`](https://github.com/Entif-AI/Bilqis-MLX/commit/7d7172a8369c4a25462779ebb5daf445c662c563) `fix(bamf): count tracked repairs after parent PR closure`
- [`ae36ceba7252`](https://github.com/Entif-AI/Bilqis-MLX/commit/ae36ceba72528b5923c65cdfa9edaa59051b7f1a) `docs(bamf): track EGM state with issue labels`
- [`0b0a942122af`](https://github.com/Entif-AI/Bilqis-MLX/commit/0b0a942122af24eac3df3aed5f606ead1065dafb) `governance(bamf): reserve PRs for real integration work`
- [`6d3ba3ae4e0f`](https://github.com/Entif-AI/Bilqis-MLX/commit/6d3ba3ae4e0fde428296435e610718cce1e80fde) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/bamf02-c12-526-exchange-20261101`
- [`7a2ac49c3786`](https://github.com/Entif-AI/Bilqis-MLX/commit/7a2ac49c37865023d88d1b1af8b9cf285e4d10cf) `fix(runtime): bind delta receiver to published generation`
- [`b7c792a1dc08`](https://github.com/Entif-AI/Bilqis-MLX/commit/b7c792a1dc08865558ea986e82d2dd9e40deee9d) `fix(bamf): make C05 screening execution-owned (#744)`
- [`6cf19868641a`](https://github.com/Entif-AI/Bilqis-MLX/commit/6cf19868641aa6d3009e9fc63ad7baf66a3f337f) `chore(bamf): checkpoint C12 remediation state`
- [`e0b15b6dfdf4`](https://github.com/Entif-AI/Bilqis-MLX/commit/e0b15b6dfdf45b5744fca6513a5dc1dfb7998e1b) `feat(governance): bound PR inventory and enforce drain`
- [`6caf1f7ac6c2`](https://github.com/Entif-AI/Bilqis-MLX/commit/6caf1f7ac6c22f636ec217968c1e5517a60992b2) `feat(bamf): remediation - enforce immediate B11 selected-state chaining`
- [`2800946729e4`](https://github.com/Entif-AI/Bilqis-MLX/commit/2800946729e484875f7d1f57f0e6d85078936394) `ci(bamf): track EGM state with issue labels`
- [`f94615dd4888`](https://github.com/Entif-AI/Bilqis-MLX/commit/f94615dd48886f269586c6fd4c05b03601b493de) `fix(bamf): bind exports to A12 source authority (#745)`
- [`21bd729f1de8`](https://github.com/Entif-AI/Bilqis-MLX/commit/21bd729f1de8e91d0143c6d6477745c842153439) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/745-a12-export-clearance-20261102`
- [`838c6259d933`](https://github.com/Entif-AI/Bilqis-MLX/commit/838c6259d93384e94aa4f50d45ffb2bf4ef9f93e) `chore(bamf): checkpoint A12 export-clearance turn-in`
- [`5b268d118a93`](https://github.com/Entif-AI/Bilqis-MLX/commit/5b268d118a93259b31c76331d51796f2e54a73a1) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/746-c12-import-commit-20261102`
- [`ac89d382137e`](https://github.com/Entif-AI/Bilqis-MLX/commit/ac89d382137e6581725d6f06220329e957fe0e7c) `Merge reviewed unified into B11 #586 candidate`
- [`d68e4fdc4616`](https://github.com/Entif-AI/Bilqis-MLX/commit/d68e4fdc461618119c40ad29702612c8b67bb3ce) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/b07-456-source-bridge-20261101`
- [`f7fd94b06f56`](https://github.com/Entif-AI/Bilqis-MLX/commit/f7fd94b06f56909fca04016731dbe4c85a38f7e2) `docs(bamf): activate B07.1 merge-readiness refresh`
- [`5d7db7d844f0`](https://github.com/Entif-AI/Bilqis-MLX/commit/5d7db7d844f0b6569f2b588e839c5816fbdadf14) `chore(bamf): reconcile merged remediation before B07.1 admission`
- [`0c88e2b6b74a`](https://github.com/Entif-AI/Bilqis-MLX/commit/0c88e2b6b74a1d0368977238fd34f3aed6afa1c2) `fix(bamf): close B07 exact-head EGM blockers`
- [`06a736120a94`](https://github.com/Entif-AI/Bilqis-MLX/commit/06a736120a940ad3e454b4c6bbfa980d5ac75778) `fix(bamf): preserve nested motif structure and custody`
- [`0f955f30929f`](https://github.com/Entif-AI/Bilqis-MLX/commit/0f955f30929fcfaebe50bf4f8d074754ac097ee6) `test(bamf): use canonical source frames in B11 receipt proofs`
- [`966d09a734b6`](https://github.com/Entif-AI/Bilqis-MLX/commit/966d09a734b6c9d561aa6af240825bcd7012e044) `fix(bamf): bind B11 receipts to executed tensor layout`
- [`0b8751df9e2e`](https://github.com/Entif-AI/Bilqis-MLX/commit/0b8751df9e2ee7d42ba721f8e9db1242d43e79aa) `refactor(bamf): split atlas engram owner modules`
- [`f1d2cf4b00a1`](https://github.com/Entif-AI/Bilqis-MLX/commit/f1d2cf4b00a11dffd3235e9e489401a9dbeac429) `fix(bamf): allocate missing structural motif keys`
- [`9d4faac6a601`](https://github.com/Entif-AI/Bilqis-MLX/commit/9d4faac6a601319a0fbad20d73a1d6fc1b1b4a54) `refactor(bamf): align engram private imports`
- [`6a51503bab0c`](https://github.com/Entif-AI/Bilqis-MLX/commit/6a51503bab0c6ad6b24a2205fecc30686c8f87ae) `docs(bamf): consume B11 EGM remediations`
- [`7e117da18f28`](https://github.com/Entif-AI/Bilqis-MLX/commit/7e117da18f287ca7f6ce5f9951543ca01bddac89) `test(bamf): restore B07 allocation acceptance surface`
- [`c99e7f669dc6`](https://github.com/Entif-AI/Bilqis-MLX/commit/c99e7f669dc650073e34a924725ecc2c44dae0d0) `docs(bamf): retire merged remediation PR inventory`
- [`c40eefd0467a`](https://github.com/Entif-AI/Bilqis-MLX/commit/c40eefd0467a83af09f50c35a99498f8da4c12eb) `fix(bamf): preserve nested motif structure on reads`
- [`203c53eb1252`](https://github.com/Entif-AI/Bilqis-MLX/commit/203c53eb1252ada8fba8ed6f1e9c7c5c57ca6cde) `chore(bamf): turn in B07.1 delivery`
- [`d87859c75177`](https://github.com/Entif-AI/Bilqis-MLX/commit/d87859c75177cd807aaaa649efb8b64fa05105b6) `docs(bamf): track live B11 and B07 PR inventory`
- [`2d4b99f3b7f8`](https://github.com/Entif-AI/Bilqis-MLX/commit/2d4b99f3b7f8f82857028a7c1f31c1e5da61b23b) `feat(bamf): execution-owned backbone group receipts (B11.1a)`
- [`e4484e5da1a9`](https://github.com/Entif-AI/Bilqis-MLX/commit/e4484e5da1a9b7e982a89aa85b08bd50c67d98cd) `fix(bamf): resolve source rows through canonical owners`
- [`4f8abf446993`](https://github.com/Entif-AI/Bilqis-MLX/commit/4f8abf446993a7f6d205e4ce50346fde88db8362) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/745-a12-export-clearance-20261102`
- [`3d32774bfde8`](https://github.com/Entif-AI/Bilqis-MLX/commit/3d32774bfde897d1cfab590e257d509c014c5259) `chore(bamf): track source-owner mitigation PR`
- [`eae3be49e6cb`](https://github.com/Entif-AI/Bilqis-MLX/commit/eae3be49e6cb38d68634bbe3175bf16e9b9ac178) `chore(bamf): retire merged B11 PR inventory`
- [`3399fbbc0e2f`](https://github.com/Entif-AI/Bilqis-MLX/commit/3399fbbc0e2f9575c3103d76f60a43f8dd7b4e4f) `chore(bamf): track source-owner mitigation PR`
- [`335361d60a3f`](https://github.com/Entif-AI/Bilqis-MLX/commit/335361d60a3f4d7050acf01c471f1f94d93a0294) `chore(bamf): retire merged B11 PR inventory`
- [`e6d3215c395a`](https://github.com/Entif-AI/Bilqis-MLX/commit/e6d3215c395a67728830b472344bb11697b2ca88) `chore(bamf): turn in A12 export clearance`
- [`349ac665880d`](https://github.com/Entif-AI/Bilqis-MLX/commit/349ac665880dbdd545cddd0ec8e50817095d73b1) `fix(bamf): content-address generation tensor custody`
- [`2b18f5ca76be`](https://github.com/Entif-AI/Bilqis-MLX/commit/2b18f5ca76be2d8d4bb39a44ca67b9d102135996) `fix(bamf): preserve error control plane in source owner resolution`
- [`8641343c0516`](https://github.com/Entif-AI/Bilqis-MLX/commit/8641343c0516f15e779e60e6b65967fe344e6a66) `chore(bamf): turn in A12 export clearance`
- [`fc899edcde93`](https://github.com/Entif-AI/Bilqis-MLX/commit/fc899edcde930d4f8e9064af817b30145dda6fc8) `chore(bamf): merge current unified into 713 remediation candidate`
- [`6a9f830fddd3`](https://github.com/Entif-AI/Bilqis-MLX/commit/6a9f830fddd39f5da441c61e0a0924584e4f6d47) `refactor(bamf): keep frame compilation helpers and proofs bounded`
- [`1378d8b60428`](https://github.com/Entif-AI/Bilqis-MLX/commit/1378d8b60428451c3d661f06ed346301d2327ffb) `fix(bamf): independently construct qualified world rule gold`
- [`4ea003f0c353`](https://github.com/Entif-AI/Bilqis-MLX/commit/4ea003f0c353a4ffccfe52e6b717f31ce7cfd800) `feat(bamf): resolve raw source rows through canonical owners`
- [`dfc0c7586c23`](https://github.com/Entif-AI/Bilqis-MLX/commit/dfc0c7586c23b6477c08d4db486ade3deeb79fae) `feat(bamf): bind A12 export clearance to source authority`
- [`719cf3014321`](https://github.com/Entif-AI/Bilqis-MLX/commit/719cf3014321a7b456d582e9076e50f462729f4c) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/758-oracle-proof-20261102`
- [`8f725693177b`](https://github.com/Entif-AI/Bilqis-MLX/commit/8f725693177b3d015c00123cd85f3eccc4fbfac9) `fix(bamf): close A08 family integration proof gaps`
- [`1e0604bcbcfd`](https://github.com/Entif-AI/Bilqis-MLX/commit/1e0604bcbcfd26f2cbfd09f45803c6a6346686da) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/participation-711-20261102`
- [`f7050207c60b`](https://github.com/Entif-AI/Bilqis-MLX/commit/f7050207c60bf0331f16c8bf01e7d4269b67acce) `chore(bamf): activate verified C10 structural candidate`
- [`af5e3ce42a24`](https://github.com/Entif-AI/Bilqis-MLX/commit/af5e3ce42a244c8c3280dce06f7622e67c2193d1) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/bamf02-c-runtime`
- [`ee37d1fa7e9c`](https://github.com/Entif-AI/Bilqis-MLX/commit/ee37d1fa7e9c7826ea03bb84f21d22cd1d39e7a1) `Merge commit 'aa2aec1809256a6270bb8afedc87c2a655175054' into codex/bamf02-c10-641-final-20261103`
- [`fef9e73ca018`](https://github.com/Entif-AI/Bilqis-MLX/commit/fef9e73ca018702aa37c450e425efe5fe5f42576) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/746-c12-import-commit-20261102`
- [`737b21a709a4`](https://github.com/Entif-AI/Bilqis-MLX/commit/737b21a709a455e87038d4df56f1bfc0e9233558) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/753-tensor-cas-20261102`
- [`cc8d36f0446e`](https://github.com/Entif-AI/Bilqis-MLX/commit/cc8d36f0446e2d82b09a83a017ba49dd76753707) `test(bamf): prove depth identity repair on accepted successor`
- [`5002b7dc3adb`](https://github.com/Entif-AI/Bilqis-MLX/commit/5002b7dc3adbb6af37140c3b293aed4011407cc2) `fix(runtime): preserve public selector pickle identities`
- [`6b980d986c0a`](https://github.com/Entif-AI/Bilqis-MLX/commit/6b980d986c0abad8f41004c5fd1fe0af6a5c8c09) `fix(bamf): freeze world capability roots`
- [`4099487b16c6`](https://github.com/Entif-AI/Bilqis-MLX/commit/4099487b16c6a26cec1888d23310ede7792bb248) `test(bamf): bind selector remediation to complete public identity proof`
- [`0ea77e24d453`](https://github.com/Entif-AI/Bilqis-MLX/commit/0ea77e24d453b14c3a52966a0dd95e4edd63e0a5) `fix(storage): durably publish tensor CAS directories`
- [`1199607a0437`](https://github.com/Entif-AI/Bilqis-MLX/commit/1199607a04379ed2a0b8f2453e7c5476282ef282) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/713-mergeforward-20261102`
- [`6c1f0777ab52`](https://github.com/Entif-AI/Bilqis-MLX/commit/6c1f0777ab52742d41fc111cfffa842c56ec4958) `chore(bamf): turn in verified C10 structural candidate`
- [`37efe5b00c28`](https://github.com/Entif-AI/Bilqis-MLX/commit/37efe5b00c285c38a0ef5d2c909385377cbd4ace) `chore(bamf): reconcile concurrent B13 delivery inventory`
- [`338a3c526377`](https://github.com/Entif-AI/Bilqis-MLX/commit/338a3c5263772566502af70d731b95af1d91a81e) `fix(runtime): preserve depth public identities on current unified`
- [`ab7d397e5339`](https://github.com/Entif-AI/Bilqis-MLX/commit/ab7d397e53390be1618e674e7dac977518591746) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/753-tensor-cas-20261102`
- [`14c730bb580e`](https://github.com/Entif-AI/Bilqis-MLX/commit/14c730bb580e0ce5f13e047db57617b0e873f2d3) `chore(bamf): reconcile live flow-control inventory`
- [`0a38241190da`](https://github.com/Entif-AI/Bilqis-MLX/commit/0a38241190da0e0238dee122c1624d780214b20a) `chore(bamf): retire accepted depth proof and activate C01`
- [`fec0a472a715`](https://github.com/Entif-AI/Bilqis-MLX/commit/fec0a472a71571b60e8cb44deaec60800fc66f22) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/bamf02-c-runtime`
- [`1ace89bcfa93`](https://github.com/Entif-AI/Bilqis-MLX/commit/1ace89bcfa938e4c4375f7a6a18f0673198e56c6) `Merge commit 'cb536f744008c7e7575c3d3973c135aa38292fd6' into codex/bamf02-c01-347-final-20261103`
- [`34f4740d0e7f`](https://github.com/Entif-AI/Bilqis-MLX/commit/34f4740d0e7fcd8ee1720047fd943581dea3fc8a) `docs(bamf): make C01 source and wheel proofs reproducible`
- [`ac1bdf5f8742`](https://github.com/Entif-AI/Bilqis-MLX/commit/ac1bdf5f8742f23fa3e7c8853154d03924a97d76) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/713-mergeforward-20261102`
- [`deaa8b9dbd27`](https://github.com/Entif-AI/Bilqis-MLX/commit/deaa8b9dbd277993f884abeea7413f9cb799d945) `fix(bamf): store generation tensors in content-addressed custody`
- [`ad787b294b4b`](https://github.com/Entif-AI/Bilqis-MLX/commit/ad787b294b4b7d7d279e4f6388656c39c5604864) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/758-oracle-proof-20261102`
- [`0bd9dfec776b`](https://github.com/Entif-AI/Bilqis-MLX/commit/0bd9dfec776b0e11679fda89d90fe1c116e583ad) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/bamf02-c01-347-final-20261103`
- [`46100a69737a`](https://github.com/Entif-AI/Bilqis-MLX/commit/46100a69737a6749df64e4364f2e05de3be24afe) `Merge commit '338a3c5263772566502af70d731b95af1d91a81e' into cos/worktrees/71e09b18559f45c7a1b9fe6ebe47dd77/worker-2`
- [`4dbff6b64a66`](https://github.com/Entif-AI/Bilqis-MLX/commit/4dbff6b64a66b0ca28fa8d326a233798836a83cb) `fix(custody): isolate tensor objects and converge concurrent adoption`
- [`670cdced77e3`](https://github.com/Entif-AI/Bilqis-MLX/commit/670cdced77e392aaee9dd8d190119aba11764730) `docs(bamf): bind C01 refresh to current source and inherited gates`
- [`cfe7e7ed98f7`](https://github.com/Entif-AI/Bilqis-MLX/commit/cfe7e7ed98f7d3928b50e33c871d56357361e32c) `docs(bamf): record clean-archive C01 source proof`
- [`3f5b79c48892`](https://github.com/Entif-AI/Bilqis-MLX/commit/3f5b79c488926dcb08cc41d40aad91978615b650) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/bamf02-c-runtime`
- [`3106a8f18c4e`](https://github.com/Entif-AI/Bilqis-MLX/commit/3106a8f18c4ee1984f3105d42d9725a9b4e50823) `fix(factory): require attested world rule authority`
- [`79bc36afeb86`](https://github.com/Entif-AI/Bilqis-MLX/commit/79bc36afeb8644c953f65cad6424716f487c2416) `fix(custody): bind reused tensor objects to durable ownership`
- [`10a416182aeb`](https://github.com/Entif-AI/Bilqis-MLX/commit/10a416182aebd236f60dc3401cb7640c6b98fa4e) `fix(bamf): bind C02 to pinned A06 feature authority`
- [`3552c5830cbe`](https://github.com/Entif-AI/Bilqis-MLX/commit/3552c5830cbeb380f1888902c4b99bc5dbadba35) `feat(bamf): commit screened package imports`
- [`3f729ca9c1de`](https://github.com/Entif-AI/Bilqis-MLX/commit/3f729ca9c1de28334cfd22800b127835503feed2) `fix(custody): detach unowned race winners before reuse`
- [`7b71fa956d08`](https://github.com/Entif-AI/Bilqis-MLX/commit/7b71fa956d088d1cfcaddf4636598327a2697943) `fix(custody): establish legacy CAS ownership before cold tensor reads`
- [`8fe94c850a28`](https://github.com/Entif-AI/Bilqis-MLX/commit/8fe94c850a287176655494fde25b09b9f2a20fbf) `fix(semantics): preserve relocated public callable identities`
- [`88ad90bb2590`](https://github.com/Entif-AI/Bilqis-MLX/commit/88ad90bb25906759bd8164670c0d6a27aa84c0d2) `fix(semantics): keep identity restoration private to facades`
- [`1c7486a2a505`](https://github.com/Entif-AI/Bilqis-MLX/commit/1c7486a2a5055d52c81ef0d1c15cfa41042c36c7) `docs(bamf): distinguish historical and later wheel receipts`
- [`c3397e7b8823`](https://github.com/Entif-AI/Bilqis-MLX/commit/c3397e7b8823e52fa2a57e6e12c00ec0b1676351) `test(custody): assert historical writer identity through unittest`
- [`3174c36897ac`](https://github.com/Entif-AI/Bilqis-MLX/commit/3174c36897ac0a67c630175692cf39cf58dcf4de) `fix(semantics): retain foreign callable module metadata`
- [`3c9f2400c046`](https://github.com/Entif-AI/Bilqis-MLX/commit/3c9f2400c046e99f8770c40004a39a2e5b6ec781) `docs(bamf): bind callable repair to no-skip source and wheel proof`
- [`4cde8c1079ee`](https://github.com/Entif-AI/Bilqis-MLX/commit/4cde8c1079eed46a7fa65a46f8b0756e6b164fad) `fix(custody): serialize reserve decisions with tensor writes`
- [`d9b71f7a30e6`](https://github.com/Entif-AI/Bilqis-MLX/commit/d9b71f7a30e639c47291edccc153ecef58dd7b6f) `style(tests): remove trailing fixture whitespace`
- [`6acd30544f6f`](https://github.com/Entif-AI/Bilqis-MLX/commit/6acd30544f6f81cb1c1b08524b53f567bd1e0cc0) `docs(bamf): bound EGM convergence episodes`
- [`a52943a5671c`](https://github.com/Entif-AI/Bilqis-MLX/commit/a52943a5671ca5a8734d40fdc9e2f87cd9553f73) `docs(bamf): tighten tensor custody evidence wording`
- [`6c8d12d6dd4c`](https://github.com/Entif-AI/Bilqis-MLX/commit/6c8d12d6dd4c8941527dd57284aea9fb0da42717) `chore(bamf): record tensor custody turn-in and live inventory`
- [`ea1f154ceb67`](https://github.com/Entif-AI/Bilqis-MLX/commit/ea1f154ceb67db899f7bc75fa2ee96fe8b5050f7) `Merge remote-tracking branch 'origin/codex/bamf02-b-769-cas-ownership-20261103' into codex/bamf02-b-769-cas-ownership-20261103`
- [`e2658aabf715`](https://github.com/Entif-AI/Bilqis-MLX/commit/e2658aabf715dcb72afa1efeb20a2b2c18c04208) `fix(source): derive fragile replay bounds from contracts`
- [`f7a7adfdbfdb`](https://github.com/Entif-AI/Bilqis-MLX/commit/f7a7adfdbfdb8d85cc30b938b2bf5ba841d70391) `ci(bamf): bound BAMF EGM convergence episodes`
- [`18cc1c0fe35b`](https://github.com/Entif-AI/Bilqis-MLX/commit/18cc1c0fe35be7096fdf951b39ce20e1667ff779) `fix(custody): isolate tensor CAS ownership and serialize reserve checks`
- [`35c172c2cfdd`](https://github.com/Entif-AI/Bilqis-MLX/commit/35c172c2cfddcd55c35f980452c4916b2f1fc44b) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/758-oracle-proof-20261102`
- [`2a26dd1c1079`](https://github.com/Entif-AI/Bilqis-MLX/commit/2a26dd1c10799bd5946428aebe90cee2f2378dae) `docs(bamf): record bounded EGM in ADR-127`
- [`b586e1be267e`](https://github.com/Entif-AI/Bilqis-MLX/commit/b586e1be267ef7ca47ef6f312bdae692c8a3d7d0) `docs(bamf): make repaired proof success predicates explicit`
- [`640c7a13fe98`](https://github.com/Entif-AI/Bilqis-MLX/commit/640c7a13fe9811b65c248f531bf5986fada48e4e) `docs(bamf): record verified recipe predicate consumption`
- [`ef5a89ebfc52`](https://github.com/Entif-AI/Bilqis-MLX/commit/ef5a89ebfc520068a01507aa05f41e43f32b4922) `test(custody): prove hard-link aliases cannot retain ownership`
- [`53655a7a5d51`](https://github.com/Entif-AI/Bilqis-MLX/commit/53655a7a5d513403bcd14e9ffd2e5577411c5832) `ci(bamf): record bounded EGM policy in ADR-127`
- [`3c1846829084`](https://github.com/Entif-AI/Bilqis-MLX/commit/3c1846829084fad994b01f4a75d60779205698bd) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/758-oracle-proof-20261102`
- [`ebe1186d4346`](https://github.com/Entif-AI/Bilqis-MLX/commit/ebe1186d4346f7c74f8f5f227ed7d9c2081364fc) `chore(bamf): track reopened tensor custody proof PR`
- [`e3b0be112883`](https://github.com/Entif-AI/Bilqis-MLX/commit/e3b0be112883e91b49a5968cdcad19b28849d65c) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/bamf02-c01-347-final-20261103`
- [`0bc2ff7fa599`](https://github.com/Entif-AI/Bilqis-MLX/commit/0bc2ff7fa599f23d15da58b1a4cd382080c114ea) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/769-hardlink-proof-20261103`
- [`13b67a5994d1`](https://github.com/Entif-AI/Bilqis-MLX/commit/13b67a5994d1a06aac26dda42968c8e4139bff64) `test(bamf): enforce current proof recipe predicates mechanically`
- [`9f7d43187d54`](https://github.com/Entif-AI/Bilqis-MLX/commit/9f7d43187d542a2be6527544fe365f52f2804676) `chore(bamf): reconcile live PR inventory`
- [`19c42edb73f0`](https://github.com/Entif-AI/Bilqis-MLX/commit/19c42edb73f0086d6baf2065eb3e58ce0385e90e) `test(custody): isolate hard-link ownership proof`
- [`fe4dcd0b21a3`](https://github.com/Entif-AI/Bilqis-MLX/commit/fe4dcd0b21a3de8e47c0bcf43f9681a92b6a556f) `chore(bamf): refresh live integration inventory`
- [`e89ea51b0566`](https://github.com/Entif-AI/Bilqis-MLX/commit/e89ea51b0566e628b6cc121bbc4c291852c378d6) `chore(bamf): track A08.3 mitigation PR`
- [`1cbb66d12da1`](https://github.com/Entif-AI/Bilqis-MLX/commit/1cbb66d12da1375c40ba10138f4326f234640c9d) `chore(bamf): track A08.3 mitigation PR`
- [`41373ef911bb`](https://github.com/Entif-AI/Bilqis-MLX/commit/41373ef911bb37c971a21fa3c7b540b923abf853) `test(custody): prove hard-link aliases cannot retain ownership`
- [`eb4ff18fa30c`](https://github.com/Entif-AI/Bilqis-MLX/commit/eb4ff18fa30c5cefe924fd69ad8628409710293c) `Merge branch 'codex/bamf-unified-base-20261028' into codex/758-oracle-proof-20261102`
- [`48315ee7bae3`](https://github.com/Entif-AI/Bilqis-MLX/commit/48315ee7bae3caa7d5ac279128c79217b9178d16) `fix(factory): qualify independent world rules through typed families`
- [`29ebe189e7ad`](https://github.com/Entif-AI/Bilqis-MLX/commit/29ebe189e7adfe46aa9b619693873f4c55c5a09c) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/746-c12-import-commit-20261102`
- [`7b57f06e7e0b`](https://github.com/Entif-AI/Bilqis-MLX/commit/7b57f06e7e0bb2c296d0eb526e00a96343f195dc) `refactor(bamf): split C09 revalidation owner`
- [`03497e3f6e91`](https://github.com/Entif-AI/Bilqis-MLX/commit/03497e3f6e911d08ee386d2e999d005d11f96a51) `feat(bamf): commit accepted package imports through B13`
- [`3df9aadb5946`](https://github.com/Entif-AI/Bilqis-MLX/commit/3df9aadb59465370314177dae15f66b718142cf2) `chore(bamf): park package import on production caller`
- [`3c19ab9ed74f`](https://github.com/Entif-AI/Bilqis-MLX/commit/3c19ab9ed74fe3f2972761073d209055868460cf) `Merge remote-tracking branch 'origin/codex/746-c12-import-commit-20261102' into codex/746-c12-import-commit-20261102`
- [`b6e616626bcb`](https://github.com/Entif-AI/Bilqis-MLX/commit/b6e616626bcbfdf17d314aa4f4f0ce257ae2ef3a) `chore(bamf): park package import on production caller`
- [`17316c9217d7`](https://github.com/Entif-AI/Bilqis-MLX/commit/17316c9217d7f65988736384ff8b447c46dad14b) `test(bamf): prove future-group independence with paired executions`
- [`f420f58a579a`](https://github.com/Entif-AI/Bilqis-MLX/commit/f420f58a579a166a9fdc251ada2fc1cf4549d63e) `chore(bamf): activate B05 depth proof integration`
- [`551f9d7f6172`](https://github.com/Entif-AI/Bilqis-MLX/commit/551f9d7f6172113b2c2698178c870cf61c7c35a0) `test(bamf): preserve source proof imports under file runner`
- [`393e473ed75e`](https://github.com/Entif-AI/Bilqis-MLX/commit/393e473ed75e23ebd78bc3156e98ff5081fb03f6) `chore(bamf): track source proof import PR`
- [`4126cdaecd92`](https://github.com/Entif-AI/Bilqis-MLX/commit/4126cdaecd92b2c515693540fb86fd09fde6338d) `docs(bamf): bind depth proof to accepted B11 producer`
- [`1607068b1665`](https://github.com/Entif-AI/Bilqis-MLX/commit/1607068b166541a6283695e452da721bbf7482f8) `chore(bamf): record depth proof turn-in and accepted producer`
- [`d1056d863335`](https://github.com/Entif-AI/Bilqis-MLX/commit/d1056d86333531431143cd0901fcdfb561b3141b) `chore(bamf): reconcile concurrent depth proof PR inventory`
- [`c08aabb9bf13`](https://github.com/Entif-AI/Bilqis-MLX/commit/c08aabb9bf13524c8f3ae71a2d1b2bed3d68493e) `merge(bamf): synchronize C01 verifier feature with reviewed unified`
- [`948f87ef4647`](https://github.com/Entif-AI/Bilqis-MLX/commit/948f87ef464704651f96fa3214b12c348593da91) `fix(bamf): verify accepted late-child contracts against pinned evidence`
- [`2d8dada3c55d`](https://github.com/Entif-AI/Bilqis-MLX/commit/2d8dada3c55df6bc87798e6d0c9a5c568b2cbb33) `chore(bamf): preserve verified C01 repair for parent consumption`
- [`c2fe40685efb`](https://github.com/Entif-AI/Bilqis-MLX/commit/c2fe40685efb37cf9394df5540078040f0e0df9e) `fix(bamf): report only verified contract-count postconditions`
- [`edae9d43fe10`](https://github.com/Entif-AI/Bilqis-MLX/commit/edae9d43fe104d8e8fdc125fc6df0b7e428ac7be) `test(bamf): restore source-atoms proof through the canonical runner`
- [`aa828eb5cb88`](https://github.com/Entif-AI/Bilqis-MLX/commit/aa828eb5cb8822a5614aa3353864bf187f83444d) `test(bamf): complete depth selection future-group proof`
- [`72d4dd1e802f`](https://github.com/Entif-AI/Bilqis-MLX/commit/72d4dd1e802fb599dd12043d7a9e8ed6d691c367) `chore(bamf): activate verified C01 repair after queue drains`
- [`4afc6c1f7df3`](https://github.com/Entif-AI/Bilqis-MLX/commit/4afc6c1f7df39159c4d24699714cbdfd0242b057) `merge(bamf): consume accepted depth and proof-runner integration`
- [`0e6b08f14f42`](https://github.com/Entif-AI/Bilqis-MLX/commit/0e6b08f14f42cf19832eca84b50b1ca9f30c93ff) `docs(bamf): describe current C01 turn-in gate`
- [`54bb14260039`](https://github.com/Entif-AI/Bilqis-MLX/commit/54bb14260039803187dd8d3e65eeec8c76527755) `docs(bamf): pin current accepted C01 verification base`
- [`c83a705ddc52`](https://github.com/Entif-AI/Bilqis-MLX/commit/c83a705ddc522e5da964c4d83a842f953cee20c8) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/737-a08-lifecycle-20261103`
- [`8a198dd46254`](https://github.com/Entif-AI/Bilqis-MLX/commit/8a198dd462542ae62d639136797f2b879a7745ba) `chore(bamf): track C01 contract verifier PR`
- [`d9e62f820379`](https://github.com/Entif-AI/Bilqis-MLX/commit/d9e62f820379b3cab8232d6377397db15d614b83) `chore(bamf): activate B07 custody integration`
- [`f101c290c558`](https://github.com/Entif-AI/Bilqis-MLX/commit/f101c290c558235de85b4049e6723a285581ab2f) `merge(bamf): retain CAS lookup and authenticated B07 continuation`
- [`12565903b889`](https://github.com/Entif-AI/Bilqis-MLX/commit/12565903b88944510b4652c7d9a61a343ede362c) `fix(bamf): preserve A08 provider resume after merge-forward`
- [`93d3fe62df1b`](https://github.com/Entif-AI/Bilqis-MLX/commit/93d3fe62df1be9f8aae995aa8446bac1bea427ea) `chore(bamf): track A08.3 lifecycle PR`
- [`82806ab55b5e`](https://github.com/Entif-AI/Bilqis-MLX/commit/82806ab55b5eef7afbc09ad6c22f8f61c399a427) `test(bamf): expose retained-state module identity drift`
- [`66f898132848`](https://github.com/Entif-AI/Bilqis-MLX/commit/66f8981328485828d5aa8503588b72f56722d4d5) `merge(bamf): consume exact B07 integration regression`
- [`17be8a3d5aeb`](https://github.com/Entif-AI/Bilqis-MLX/commit/17be8a3d5aebfaba0a88b4190a41027eb6daedfb) `fix(bamf): preserve canonical retained-state identity across custody`
- [`bcae1037a434`](https://github.com/Entif-AI/Bilqis-MLX/commit/bcae1037a434f886df4e84444cd2dc26daa42dde) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/bamf02-c-runtime`
- [`62d65eb2dac4`](https://github.com/Entif-AI/Bilqis-MLX/commit/62d65eb2dac48dbd7da5ff6f6770c4a1b1359c02) `Merge remote-tracking branch 'origin/codex/bamf02-c01-347-final-20261103' into codex/bamf02-c-347-integration-20261103`
- [`47188f534045`](https://github.com/Entif-AI/Bilqis-MLX/commit/47188f5340450eeab189995456b14979ad078216) `Merge remote-tracking branch 'origin/codex/bamf02-c-770-contract-verifier-20261103' into codex/bamf02-c-347-integration-20261103`
- [`a59031047b19`](https://github.com/Entif-AI/Bilqis-MLX/commit/a59031047b19903ad09b74376608bf70e86b0517) `docs(bamf): record combined C01 structural and verifier proof`
- [`afbde3e58034`](https://github.com/Entif-AI/Bilqis-MLX/commit/afbde3e58034316bb962b1f7eb3a9f201583e255) `chore(bamf): select canonical C02 authority repair for verification`
- [`10375fcc7f0b`](https://github.com/Entif-AI/Bilqis-MLX/commit/10375fcc7f0b54bd3cf2e9ecad1820eb465fd76d) `Merge remote-tracking branch 'origin/codex/713-mergeforward-20261102' into codex/bamf02-c-713-authority-20261103`
- [`b0f7ce3b4cf7`](https://github.com/Entif-AI/Bilqis-MLX/commit/b0f7ce3b4cf795693c16d3efa84725e4087bff40) `docs(bamf): preserve C02 source-authority review blocker`
- [`75a93428c9ad`](https://github.com/Entif-AI/Bilqis-MLX/commit/75a93428c9ad6e0fe286187d7c043e893ed0aeb3) `docs(bamf): route feature selection authority to canonical A06 owner`
- [`9eb8fa5b935c`](https://github.com/Entif-AI/Bilqis-MLX/commit/9eb8fa5b935c4e7be8983e71dcf69a3fc7c3add3) `chore(bamf): select consumed C01 parent for combined integration`
- [`5340e0967c26`](https://github.com/Entif-AI/Bilqis-MLX/commit/5340e0967c263eaf159979eab9c516090bc0c87f) `docs(bamf): preserve failed C01 round-three findings and coverage`
- [`6f0dd50d5def`](https://github.com/Entif-AI/Bilqis-MLX/commit/6f0dd50d5def762bf4824868c5d635c56a58a5ac) `fix(semantics): preserve public released-schema verification hooks`
- [`d2d2a0bf5526`](https://github.com/Entif-AI/Bilqis-MLX/commit/d2d2a0bf5526b5c7fd690f0d9f3069f0dd8fcd84) `fix(bamf): validate declared recipe totals across proof overlays`
- [`173438e31bb6`](https://github.com/Entif-AI/Bilqis-MLX/commit/173438e31bb63f50b6973e44ee044dfc2c7df1e1) `docs(bamf): bind complete C01 repairs to fresh composed proof`
- [`2765b5df6ce0`](https://github.com/Entif-AI/Bilqis-MLX/commit/2765b5df6ce0a23c9388800c13375ac2f67a98b3) `chore(bamf): reconcile exact repair custody before final review`
- [`f4d8ddfe08a1`](https://github.com/Entif-AI/Bilqis-MLX/commit/f4d8ddfe08a1d378dd0501208693af4a4aa07398) `fix(bamf): verify accepted late-child contracts from pinned evidence`
- [`9bf47289e9ed`](https://github.com/Entif-AI/Bilqis-MLX/commit/9bf47289e9ed0a64d275b31c3a7de42c55a8b83e) `fix(bamf): refresh A08.3 on current unified`
- [`c4dffbf1acf5`](https://github.com/Entif-AI/Bilqis-MLX/commit/c4dffbf1acf543378ce673f35be23c05163eebf4) `merge(bamf): sync B07/B13 identity repair with current unified`
- [`2f8754d1609d`](https://github.com/Entif-AI/Bilqis-MLX/commit/2f8754d1609dc0f1a721adb5521db67799b7139c) `test(bamf): complete B07 cold-continuation acceptance`
- [`ddd4bb411014`](https://github.com/Entif-AI/Bilqis-MLX/commit/ddd4bb411014cdd7ac5fe437d1f733478d5cbdc4) `chore(bamf): turn in B07 cold-continuation refresh`
- [`f8d4471607b1`](https://github.com/Entif-AI/Bilqis-MLX/commit/f8d4471607b14052e57385de6cd997f3856f3082) `chore(bamf): reconcile merged flow inventory`
- [`bcffdcdfa43a`](https://github.com/Entif-AI/Bilqis-MLX/commit/bcffdcdfa43a6a0f4fb9495a3c866e9d17fa8eff) `fix(bamf): bind motif continuation to custody`
- [`58209522c885`](https://github.com/Entif-AI/Bilqis-MLX/commit/58209522c8855245c3b9ae22e1a57255974ffc05) `fix(bamf): require pinned continuation manifest`
- [`c078386bd57a`](https://github.com/Entif-AI/Bilqis-MLX/commit/c078386bd57a209bb10f55142c7b1c5af94a50b1) `chore(bamf): refresh B07 turn-in receipt`
- [`14c006174e92`](https://github.com/Entif-AI/Bilqis-MLX/commit/14c006174e927d5ab2b331c4e6323757301c5fb4) `chore(bamf): activate C01 late-bound remediation`
- [`4ef19ccce5b4`](https://github.com/Entif-AI/Bilqis-MLX/commit/4ef19ccce5b4cc4217a417009a355b30eb599865) `merge(bamf): consume C01 attempt4 parent`
- [`7984d7872d49`](https://github.com/Entif-AI/Bilqis-MLX/commit/7984d7872d49b3987284692f5398da71f2a72605) `Merge pull request #690 from Entif-AI/codex/b07-456-source-bridge-20261101`
- [`37060b3d6730`](https://github.com/Entif-AI/Bilqis-MLX/commit/37060b3d6730d174253c59bcfd77de0bfdd46cc1) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/800-c01-latebound-20261103`
- [`4dcfc7169738`](https://github.com/Entif-AI/Bilqis-MLX/commit/4dcfc7169738e721df0f1df259f2d9659d54cab4) `test(bamf): reconcile expanded B01 schema through B13 custody`
- [`a4f0fa42cc1b`](https://github.com/Entif-AI/Bilqis-MLX/commit/a4f0fa42cc1b49c7b9a74cd6280e01837bcf1c7f) `docs(bamf): bind schema proof to scoped custody and review receipts`
- [`4e19623217b2`](https://github.com/Entif-AI/Bilqis-MLX/commit/4e19623217b20a79f38ba30e79dfc14294171740) `chore(bamf): register B13 schema integration candidate`
- [`59cd3e73efdf`](https://github.com/Entif-AI/Bilqis-MLX/commit/59cd3e73efdf2bfb9d21f720b3573f3ca9a42935) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/bamf02-c-sync-c188-20261103`
- [`e9899fc0c2d4`](https://github.com/Entif-AI/Bilqis-MLX/commit/e9899fc0c2d459ef411835009ab81725feec1342) `chore(bamf): activate native recipe remediation`
- [`76f55ca807e4`](https://github.com/Entif-AI/Bilqis-MLX/commit/76f55ca807e457b69447d7a04c1afe94e19ee10a) `Merge remote-tracking branch 'origin/codex/bamf02-c-347-integration-20261103' into codex/bamf02-c-801-native-recipe-20261103`
- [`bd376f283197`](https://github.com/Entif-AI/Bilqis-MLX/commit/bd376f283197d8d0762a5eb453be8879e8847452) `docs(bamf): make native C01 CPU proof reproducible`
- [`70d3b398f5c0`](https://github.com/Entif-AI/Bilqis-MLX/commit/70d3b398f5c05380b16de878432d6bc25617a25e) `chore(bamf): turn in native environment recipe repair`
- [`d2d88078a042`](https://github.com/Entif-AI/Bilqis-MLX/commit/d2d88078a042687ebfad49586735b66a8c5d4926) `fix(c01): restore late-bound facade dependencies`
- [`5f9d484e94a9`](https://github.com/Entif-AI/Bilqis-MLX/commit/5f9d484e94a942f5421281187764efbdefa8ee24) `docs(c01): record late-bound facade proof`
- [`1205b9904bab`](https://github.com/Entif-AI/Bilqis-MLX/commit/1205b9904bab144679972dba1d652dfa51fed4f6) `Merge remote-tracking branch 'origin/codex/bamf02-c-801-native-recipe-20261103' into codex/bamf02-c-347-integration-20261103`
- [`102b8d261259`](https://github.com/Entif-AI/Bilqis-MLX/commit/102b8d261259e422fc573430229dc63b5357e8a0) `docs(c01): record parent native replay`
- [`c6546461eb26`](https://github.com/Entif-AI/Bilqis-MLX/commit/c6546461eb268b6cd1a06067b044d37296970328) `chore(bamf): checkpoint C01 aggregate`
- [`b9d4cf09aab1`](https://github.com/Entif-AI/Bilqis-MLX/commit/b9d4cf09aab1da127e8b326d34ca956e45145468) `test(c01): freeze facade census families`
- [`961390b4313c`](https://github.com/Entif-AI/Bilqis-MLX/commit/961390b4313cf210703d1fe7575f55dcaa03fb12) `docs(c01): scrub local proof paths`
- [`05e31a576e34`](https://github.com/Entif-AI/Bilqis-MLX/commit/05e31a576e3432e4238c9b4477a70d70ec4fc487) `test(bamf): reconcile expanded B01 schema through B13 custody`
- [`1caa9ee8a131`](https://github.com/Entif-AI/Bilqis-MLX/commit/1caa9ee8a131765922c027751b87a4914d20c32c) `feat(bamf): bind accepted-generation feature authority to source replay`
- [`d65a3b14bd99`](https://github.com/Entif-AI/Bilqis-MLX/commit/d65a3b14bd998d2661065c94f49fa0e3767aedd4) `chore(bamf): record lane B flow-control state for #708`
- [`7d8e3b988158`](https://github.com/Entif-AI/Bilqis-MLX/commit/7d8e3b98815843bc6ac8112ba6a57e251d122375) `chore(bamf): reconcile live flow-control inventory for #803 and #802`
- [`d95666ce308c`](https://github.com/Entif-AI/Bilqis-MLX/commit/d95666ce308ce6393f9d4ed9f54ccd1f4d113efc) `chore(bamf): record PR #804 for the #708 remediation`
- [`b30e5d27eccd`](https://github.com/Entif-AI/Bilqis-MLX/commit/b30e5d27eccd960cddce5fb275854008aa9ba2d4) `test(bamf): prove B13.2 cold resume through the published pointer path`
- [`dc7a2c621a26`](https://github.com/Entif-AI/Bilqis-MLX/commit/dc7a2c621a26a84a750e1ec630f31695ce9f09be) `chore(bamf): record the #709 remediation head in lane B state`
- [`ab44e11fe599`](https://github.com/Entif-AI/Bilqis-MLX/commit/ab44e11fe5998042b5aef6b5f9c35da87b2db0af) `chore(bamf): carry the live flow-control inventory into the #709 branch`
- [`37e9bb79fcc0`](https://github.com/Entif-AI/Bilqis-MLX/commit/37e9bb79fcc016575128ac2c07a66d346369e73a) `chore(bamf): record the #709 remediation leaf in lane B state`
- [`e5e3356aee5e`](https://github.com/Entif-AI/Bilqis-MLX/commit/e5e3356aee5e08478754016d505225eed4c8715f) `chore(bamf): record PR #805 for the #709 remediation`
- [`12c1c03b981e`](https://github.com/Entif-AI/Bilqis-MLX/commit/12c1c03b981ee26f77b9357d6b38e4fa67625fbb) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/remediation-711-participation-20261103`
- [`607ae8e23fde`](https://github.com/Entif-AI/Bilqis-MLX/commit/607ae8e23fdebb6bb9065b19440c079d69d69410) `chore(bamf): record the #711 participation owner on current unified`
- [`2acb9dec9161`](https://github.com/Entif-AI/Bilqis-MLX/commit/2acb9dec916136d569805458fdf50031dcb2ea6a) `chore(bamf): turn in the delivered #708 and #709 remediation items`
- [`93cf0db1f858`](https://github.com/Entif-AI/Bilqis-MLX/commit/93cf0db1f858d3c954292467c10bdb08b9b31aa8) `chore(bamf): turn in the delivered #708 and #709 remediation items`
- [`cc67e4974e22`](https://github.com/Entif-AI/Bilqis-MLX/commit/cc67e4974e22be1bb48d54362f0574ea208741ed) `chore(bamf): turn in the delivered #708 and #709 remediation items`
- [`969a488afa28`](https://github.com/Entif-AI/Bilqis-MLX/commit/969a488afa286b19683926b2922866920b277610) `chore(bamf): record owner-authorized PR admission for the EGM-Mitigation queue`
- [`101a2c574b71`](https://github.com/Entif-AI/Bilqis-MLX/commit/101a2c574b713214c8c2bc9421ea4494919af136) `chore(bamf): record PR #806 for the #711 remediation`
- [`996b6104ff76`](https://github.com/Entif-AI/Bilqis-MLX/commit/996b6104ff76313b950f4f47b3e843fc87660d56) `fix(plasticity): bind B12.2 candidate steps to owner-issued execution provenance`
- [`0a3d5c667875`](https://github.com/Entif-AI/Bilqis-MLX/commit/0a3d5c667875919f5223392afb4df2fed9a51eb1) `chore(bamf): record the #710 remediation leaf in lane B state`
- [`371d417b5eae`](https://github.com/Entif-AI/Bilqis-MLX/commit/371d417b5eae7e0f20155f7f08b45c598c890703) `chore(bamf): record PR #807 for the #710 remediation`
- [`dc57690bd688`](https://github.com/Entif-AI/Bilqis-MLX/commit/dc57690bd6881e800c7f214e47547fe7eb1cea91) `chore(bamf): resolve flow-control ledger for the #713 lane C candidate`
- [`f13abd7c8afe`](https://github.com/Entif-AI/Bilqis-MLX/commit/f13abd7c8afee13a5fdcaae86b43e1efae0dd724) `merge(bamf): reconcile C01 with current unified`
- [`0d3a6194e0b5`](https://github.com/Entif-AI/Bilqis-MLX/commit/0d3a6194e0b577345ff5c173f206ff1f8638672c) `fix(bamf): refresh the relocated owner census for the #713 lane C candidate`
- [`06b42d6cb7f5`](https://github.com/Entif-AI/Bilqis-MLX/commit/06b42d6cb7f574407323f2e8d1dd819e15ad8ced) `chore(bamf): resolve the lane A ledger conflict for the #713 candidate`
- [`7436f550c06c`](https://github.com/Entif-AI/Bilqis-MLX/commit/7436f550c06c797d24c79c8a0c05d64a8f5739d2) `chore(bamf): clear stale merged PR numbers from the lane ledger`
- [`0b3e301161f1`](https://github.com/Entif-AI/Bilqis-MLX/commit/0b3e301161f125d0b9754db47a3905fe028b918c) `chore(bamf): record owner-authorized PR admission for the EGM-Mitigation queue`
- [`ccec0e824e54`](https://github.com/Entif-AI/Bilqis-MLX/commit/ccec0e824e549ce5225a569cd5a6f49df5a365c9) `chore(bamf): record PR #808 for the #713 remediation`
- [`dc85028911cd`](https://github.com/Entif-AI/Bilqis-MLX/commit/dc85028911cd200c8aac7454b0defd585e79eba9) `fix(bamf): require retention acceptance before accepted-generation authority`
- [`8cc2fe7a7480`](https://github.com/Entif-AI/Bilqis-MLX/commit/8cc2fe7a748094e60deeea6e7930afc705709f10) `chore(bamf): consume the #708 acceptance binding in the #709 candidate`
- [`402b27c60bb2`](https://github.com/Entif-AI/Bilqis-MLX/commit/402b27c60bb29026b7e2ee9c2de7990cd2caaf58) `test(bamf): publish the cold-resume successor with its retention acceptance binding`
- [`238d342f8e24`](https://github.com/Entif-AI/Bilqis-MLX/commit/238d342f8e24f320f6d87f235da29f317e315e97) `feat(bamf): bind B09.2 participation to production execution owners`
- [`6a1a37004321`](https://github.com/Entif-AI/Bilqis-MLX/commit/6a1a37004321090b8fa994122cec70598c4e81e3) `chore(bamf): reconcile the live flow-control inventory for the #711 candidate`
- [`b7315f355a99`](https://github.com/Entif-AI/Bilqis-MLX/commit/b7315f355a99a7c85f006d0e30c6d54ebbf4657b) `chore(bamf): consume the B09.2 owner provenance from the #711 branch`
- [`ffbb79cdfdff`](https://github.com/Entif-AI/Bilqis-MLX/commit/ffbb79cdfdff228a1cd35a78f624c141c331927e) `feat(bamf): wire the production candidate step through the B09.2 binder`
- [`0afca5a2c389`](https://github.com/Entif-AI/Bilqis-MLX/commit/0afca5a2c389ce4b69d05b0eee9d409722ecaaa1) `chore(bamf): consolidate the #708, #709, #710 and #711 remediation leaves`
- [`31e780c2c2f2`](https://github.com/Entif-AI/Bilqis-MLX/commit/31e780c2c2f2ef590d331c7b79f705de23d96bbf) `Merge remote-tracking branch 'origin/codex/remediation-709-cold-resume-20261103' into codex/remediation-egm-708-711-integration-20261103`
- [`8530dd9bfa82`](https://github.com/Entif-AI/Bilqis-MLX/commit/8530dd9bfa824f4637f4e1ab35f738a81fbb01a2) `chore(bamf): record the consolidated integration PR #809`
- [`1dff6fbf7529`](https://github.com/Entif-AI/Bilqis-MLX/commit/1dff6fbf75298544f17fddc5f055a670d9d6612a) `chore(bamf): represent the consolidated PR #809 once in the lane ledger`
- [`c3f75a0bc9a4`](https://github.com/Entif-AI/Bilqis-MLX/commit/c3f75a0bc9a4c809b1354938f566baa4e883d86d) `docs(c01): bind final turn-in proof to current head`
- [`ac413c2d0a7a`](https://github.com/Entif-AI/Bilqis-MLX/commit/ac413c2d0a7acd7501de30ea5c44e7a558700b39) `docs(c01): bind structural branch authority`
- [`e9226be2f6a4`](https://github.com/Entif-AI/Bilqis-MLX/commit/e9226be2f6a41f47109ca02a1103a363e64909a7) `Merge pull request #803 from Entif-AI/codex/bamf02-c-347-integration-20261103`
- [`6b565ba4b416`](https://github.com/Entif-AI/Bilqis-MLX/commit/6b565ba4b4161153b2c94cefa29a986eca9a22fa) `fix(bamf): finish the production authority seams for the EGM-Mitigation leaves`
- [`1cb8e1656136`](https://github.com/Entif-AI/Bilqis-MLX/commit/1cb8e165613679c046466f5391b331b12a6cc6d8) `chore(bamf): merge forward the consolidated candidate onto current unified`
- [`11e4a7aae666`](https://github.com/Entif-AI/Bilqis-MLX/commit/11e4a7aae66618e3fd7192e7d5fb9b720b488d2d) `chore(bamf): clear the merged PR number from the lane ledger`
- [`b490712574a4`](https://github.com/Entif-AI/Bilqis-MLX/commit/b490712574a4a91fb556c6d12ec48b7f6eba764f) `fix(bamf): express the feature schema binding width as a domain contract`
- [`5afd9ce51898`](https://github.com/Entif-AI/Bilqis-MLX/commit/5afd9ce51898cebc99bda2ade28890ab157fcf40) `fix(bamf): resolve the merge-forward conflict markers in the consolidated candidate`
- [`636d62839580`](https://github.com/Entif-AI/Bilqis-MLX/commit/636d6283958038e7a285448d7a090469bd1c069a) `test(bamf): prove shared selector identity through cold custody`
- [`0956114dd35f`](https://github.com/Entif-AI/Bilqis-MLX/commit/0956114dd35f6a368a129a9c6cf179e48a536b65) `test(bamf): freeze selector census and preserve turn-in gate`
- [`537f4c627548`](https://github.com/Entif-AI/Bilqis-MLX/commit/537f4c627548168f62f0f2284e4821e52fe3afe1) `fix(bamf): bind execution, retention acceptance and step proofs to their owners`
- [`9598d87c3a7a`](https://github.com/Entif-AI/Bilqis-MLX/commit/9598d87c3a7a7ab237b777455cce2a03a326ff9c) `docs(bamf): refresh the B09.2, B12.2, B13.2 and B13.5 receipts for the consolidated head`
- [`e11137295c16`](https://github.com/Entif-AI/Bilqis-MLX/commit/e11137295c1657a2849818f4820b7878a74c120a) `docs(bamf): record the cold-resume equivalence and the retention decision owner in the receipts`
- [`6f3ebfce5b53`](https://github.com/Entif-AI/Bilqis-MLX/commit/6f3ebfce5b53b020102adb588edd7f7e0fd9359c) `chore(bamf): refresh the error catalog and field manual for the new custody codes`
- [`6ee93b27f0ea`](https://github.com/Entif-AI/Bilqis-MLX/commit/6ee93b27f0ea3e3790eefebeae4d25e58a3bd819) `test(bamf): refresh the relocated owner census for the retention decision owner`
- [`b4940b3804e0`](https://github.com/Entif-AI/Bilqis-MLX/commit/b4940b3804e0296c02b74677c4ae54286e48f290) `fix(bamf): enforce the full execution provenance identity at the candidate step`
- [`d2d7c273bd3f`](https://github.com/Entif-AI/Bilqis-MLX/commit/d2d7c273bd3f5a044796ea65efa00e038d423687) `fix(bamf): verify retained step proofs at acceptance boundaries`
- [`6b998f3444b5`](https://github.com/Entif-AI/Bilqis-MLX/commit/6b998f3444b5f7ac1d026a400e3bfe73feb330a7) `fix(bamf): distinguish parsed acceptance evidence from live authority`
- [`f23ba07055b9`](https://github.com/Entif-AI/Bilqis-MLX/commit/f23ba07055b9a1293b73a9b942290e0c57d46965) `fix(bamf): keep historical retention decisions out of live admission`
- [`a51506ab00f4`](https://github.com/Entif-AI/Bilqis-MLX/commit/a51506ab00f4852a217957b262b8fe4cbfcf01ce) `fix(bamf): bind retention decisions to C05 evaluation and parent custody`
- [`df41fe534233`](https://github.com/Entif-AI/Bilqis-MLX/commit/df41fe53423319bbf4e1234f90d24343ed07dabb) `test(bamf): preserve historical acceptance without opaque C05 indexes`
- [`9b5f89b37835`](https://github.com/Entif-AI/Bilqis-MLX/commit/9b5f89b37835c19f340667cbb1c9719f05526cd6) `fix(bamf): require execution-owned evidence for loss-bearing steps`
- [`ac01a5b35b96`](https://github.com/Entif-AI/Bilqis-MLX/commit/ac01a5b35b9657e0e5ea3be750e750ca59e693db) `docs(bamf): govern execution dashboard`
- [`bb4e3ba026a5`](https://github.com/Entif-AI/Bilqis-MLX/commit/bb4e3ba026a556178367708132ec9d7404dee4f3) `fix(bamf): anchor C05 custody and hold unqualified execution and source issuance`
- [`b7c802b0f1e9`](https://github.com/Entif-AI/Bilqis-MLX/commit/b7c802b0f1e9ce7061fefefe1fb7be8f074c57c4) `fix(bamf): exclude governance-only PR 814 from implementation inventory`
- [`9c642a8a61aa`](https://github.com/Entif-AI/Bilqis-MLX/commit/9c642a8a61aab2a134f6337d1c4bda33724ae425) `docs(bamf): close merged implementation issues`
- [`4f5f432647fb`](https://github.com/Entif-AI/Bilqis-MLX/commit/4f5f432647fb113fa8786ae5f03f57b86d512105) `docs(bamf): govern execution dashboard`
- [`490ddf82a700`](https://github.com/Entif-AI/Bilqis-MLX/commit/490ddf82a70035e45b4797b6b2ef0582b98f1ece) `chore(bamf): activate 713 for PR 808 reconciliation`
- [`34d360faffca`](https://github.com/Entif-AI/Bilqis-MLX/commit/34d360faffca5b12c829d427ddebba89aa8e204f) `chore(bamf): reconcile PR 808 with current unified`
- [`260a4440f7bf`](https://github.com/Entif-AI/Bilqis-MLX/commit/260a4440f7bf2a1d439beed3f1a33d4536236144) `fix(bamf): reconcile C02 row identity with unified`
- [`73f6a3b753f1`](https://github.com/Entif-AI/Bilqis-MLX/commit/73f6a3b753f1cd29ba9a1453b1fec1a3674894b1) `fix(bamf): reconcile live remediation inventory`
- [`18e80534d25d`](https://github.com/Entif-AI/Bilqis-MLX/commit/18e80534d25d71492566f3e757bb4ebf1bbc8340) `fix(bamf): recover source-owned execution witnesses`
- [`3ae86b2fcfd4`](https://github.com/Entif-AI/Bilqis-MLX/commit/3ae86b2fcfd4dcb7309741c162ac825b4a104584) `fix(bamf): bind loss-bearing updates to B11 execution`
- [`b0892466d10d`](https://github.com/Entif-AI/Bilqis-MLX/commit/b0892466d10dc08fb4e3c312177a6df7b85188c9) `fix(bamf): re-enter canonical A06 feature authority at the C02.1 model-input boundary`
- [`cfee1fd0ea0b`](https://github.com/Entif-AI/Bilqis-MLX/commit/cfee1fd0ea0bcf36f1238d7aeee16936a4f13655) `fix(bamf): expand PR concurrency and preserve compaction writer continuity`
- [`5cc96f478cc8`](https://github.com/Entif-AI/Bilqis-MLX/commit/5cc96f478cc84128602e61a8dc4217b5d3e3be3c) `docs(bamf): make unavailable live PR inventory nonblocking`
- [`63e45a85aa05`](https://github.com/Entif-AI/Bilqis-MLX/commit/63e45a85aa05433ee241bc5581b4c40eacc34573) `feat(bamf): verify exact-branch compaction handoff continuity`
- [`9d6560f0f1e6`](https://github.com/Entif-AI/Bilqis-MLX/commit/9d6560f0f1e6e01c55910832d0d3e7dd5587977e) `ci(bamf): reuse passing suites until invalidated`
- [`777b93a17726`](https://github.com/Entif-AI/Bilqis-MLX/commit/777b93a177260a452f4441ddfd2390df29cf71f3) `fix(bamf): place handoff helper under bounded scripts package`
- [`06eb34d0435d`](https://github.com/Entif-AI/Bilqis-MLX/commit/06eb34d0435d2f41c6f3561cf8cad6988d5b849f) `fix(bamf): restore parallel PR throughput and compaction-safe issue continuation`
- [`dd6a0ef8bf90`](https://github.com/Entif-AI/Bilqis-MLX/commit/dd6a0ef8bf90435fc20d00a5e1531a998e8402fe) `docs(bamf): close remediation issues after merge`
- [`1dafec77c4ae`](https://github.com/Entif-AI/Bilqis-MLX/commit/1dafec77c4ae833ebbb9f8d507faf13d5aa8ece1) `fix(bamf): bind source-owned B11 execution to accepted custody`
- [`52444f864dbb`](https://github.com/Entif-AI/Bilqis-MLX/commit/52444f864dbb87aca29753410023d4e79269cde7) `fix(bamf): derive B09 participation from live loss reads`
- [`f818f60ec2cf`](https://github.com/Entif-AI/Bilqis-MLX/commit/f818f60ec2cf849004dd380a03cd38ac206a6ee0) `fix(bamf): exclude unexecuted readout heads from B09`
- [`77ae274d077c`](https://github.com/Entif-AI/Bilqis-MLX/commit/77ae274d077c943de7bd81c64116914a435593a9) `refactor(factory): split executable release contract owners`
- [`e855f408a75a`](https://github.com/Entif-AI/Bilqis-MLX/commit/e855f408a75a4671156574d54e90e6c20c59ba60) `fix(factory): retain error inventory through release extraction`
- [`9ae048b18c21`](https://github.com/Entif-AI/Bilqis-MLX/commit/9ae048b18c21d19f95f82d44ecdcf53a65b1c2a0) `fix(bamf): preserve unverified handoffs for local-only branches`
- [`16e14ab6c6f0`](https://github.com/Entif-AI/Bilqis-MLX/commit/16e14ab6c6f0550112aa8786fb2b86465fdad75b) `docs(factory): bind structural review to exact test evidence`
- [`54b6d20aa486`](https://github.com/Entif-AI/Bilqis-MLX/commit/54b6d20aa486af27f53b436620ebd1ff8eb1386c) `chore(bamf): register executable release structural turn-in`
- [`f93ef4a87579`](https://github.com/Entif-AI/Bilqis-MLX/commit/f93ef4a8757999d06b4f5dfb0ae6f46f70001fcb) `fix(bamf): bind untracked symlink text in handoff fingerprints`
- [`d332ce0c7d58`](https://github.com/Entif-AI/Bilqis-MLX/commit/d332ce0c7d5833cfc685de9f71ccfcfba4dad9b2) `fix(bamf): frame typed worktree records in continuation fingerprints`
- [`30a79175cc8b`](https://github.com/Entif-AI/Bilqis-MLX/commit/30a79175cc8b54da5c54ebf23f9f52e30eda8247) `test(bamf): exercise unsupported entry after Git enumeration`
- [`3fbb3df0e4e2`](https://github.com/Entif-AI/Bilqis-MLX/commit/3fbb3df0e4e2be94ad2c6766510bb681019b988f) `fix(bamf): bind staged index entries and flags in handoff snapshots`
- [`4334288fccf3`](https://github.com/Entif-AI/Bilqis-MLX/commit/4334288fccf392585f7ae5a1fdd7d5f6b855fd88) `test(bamf): target untracked enumeration in FIFO drift fixture`
- [`6cc4161265eb`](https://github.com/Entif-AI/Bilqis-MLX/commit/6cc4161265ebfbf6d268c333570d2f894ee80e54) `chore(bamf): prepare complete handoff candidate for fourth review`
- [`1985f621ca5a`](https://github.com/Entif-AI/Bilqis-MLX/commit/1985f621ca5ac26c734a64d65693c045b870ce57) `refactor(semantics): split context eligibility and receipt owners`
- [`af4bd4ad94fb`](https://github.com/Entif-AI/Bilqis-MLX/commit/af4bd4ad94fbd0735cac496bf3273cdd5420d0a4) `fix(bamf): capture tracked paths hidden by index flags`
- [`9ed45b8fdec0`](https://github.com/Entif-AI/Bilqis-MLX/commit/9ed45b8fdec0c9c6709bf124cf0d169f1f47d8f3) `chore(bamf): record complete handoff repairs for final review`
- [`93a9f2028058`](https://github.com/Entif-AI/Bilqis-MLX/commit/93a9f20280586f84df381e0dcb63d7c96ae203ff) `chore(bamf): record context eligibility structural turn-in`
- [`75e47376d7a0`](https://github.com/Entif-AI/Bilqis-MLX/commit/75e47376d7a0977e31809291508fcdf33eb03b0e) `fix(bamf): anchor handoff capture to no-follow directory descriptors`
- [`93fe19ab2504`](https://github.com/Entif-AI/Bilqis-MLX/commit/93fe19ab2504ed6bd17156cb6f58487892ec77b7) `chore(bamf): preserve handoff design at finite review cap`
- [`feaef7d78516`](https://github.com/Entif-AI/Bilqis-MLX/commit/feaef7d78516e346030cb0e88eecfc27089e957e) `refactor(semantics): preserve context eligibility in cohesive owners`
- [`3e7471f2b461`](https://github.com/Entif-AI/Bilqis-MLX/commit/3e7471f2b46147b983c9f33a4202ee161b1bfbd6) `Merge branch 'codex/bamf-unified-base-20261028' into codex/bamf02-a-824-release-structure-20261104`
- [`e58dd31574a6`](https://github.com/Entif-AI/Bilqis-MLX/commit/e58dd31574a6ee2ce0b3e35f92293a09befd15c1) `refactor(factory): preserve executable release contracts in cohesive owners`
- [`990f5a825a89`](https://github.com/Entif-AI/Bilqis-MLX/commit/990f5a825a898f2fdaed75a275938fefbf4c039a) `fix(egm): 710 and 711 positive execution 20261104`
- [`f6dfd67daa16`](https://github.com/Entif-AI/Bilqis-MLX/commit/f6dfd67daa160e13eff0e197c35dce8bf16ef4c7) `perf(test): add differential inner-loop verification`
- [`3073cc7878c5`](https://github.com/Entif-AI/Bilqis-MLX/commit/3073cc7878c538fe813d3f8a1551b0331c3a0645) `refactor(scripts): restore directory structure limits`
- [`812b3a87337b`](https://github.com/Entif-AI/Bilqis-MLX/commit/812b3a87337ba2ef7846e4160c17f2b36c459eff) `perf(test): map transitive Python dependencies`
- [`2cc76bf82064`](https://github.com/Entif-AI/Bilqis-MLX/commit/2cc76bf82064895e8f3cfae967a63c4b9ead5c66) `ci: follow relocated release validator`
- [`85a935fd2fed`](https://github.com/Entif-AI/Bilqis-MLX/commit/85a935fd2fed66ffec1666970f208adb77b251b5) `ci: skip semantic verification for unrelated changes`
- [`791f4bbfda8e`](https://github.com/Entif-AI/Bilqis-MLX/commit/791f4bbfda8e49085a0ad6cdb8ae0899c7e54fc0) `chore(bamf): reconcile merged PR 808 inventory`
- [`7be7a77bf6cd`](https://github.com/Entif-AI/Bilqis-MLX/commit/7be7a77bf6cd546062b8dba76e6cec44018e6a88) `refactor(test): satisfy changed-file hygiene gates`
- [`57f2072fad56`](https://github.com/Entif-AI/Bilqis-MLX/commit/57f2072fad5662a1acf942ddb307ff73e5eda059) `ci: install portable semantic runtime dependency`
- [`f58a2e4ad7a0`](https://github.com/Entif-AI/Bilqis-MLX/commit/f58a2e4ad7a045ebcbf559f6073ff241c3da5eeb) `perf(test): add differential inner-loop verification`
- [`fdade5153f43`](https://github.com/Entif-AI/Bilqis-MLX/commit/fdade5153f43f9de9b21285efba3dfa3467f7c68) `chore(bamf): activate Factory execution structural interruption`
- [`9f365cbecd14`](https://github.com/Entif-AI/Bilqis-MLX/commit/9f365cbecd14eda71a3058e8ea9d9a07803361a0) `docs(bamf): gate remediation spend before issue creation`
- [`9cfb7309c094`](https://github.com/Entif-AI/Bilqis-MLX/commit/9cfb7309c094f0da90457293308a77b397051797) `docs(bamf): gate scope expansion without suppressing decomposition`
- [`5ed50357c7af`](https://github.com/Entif-AI/Bilqis-MLX/commit/5ed50357c7af0f93ee030e5daff727e15da4988b) `fix(test): preserve native package context for unique file modules`
- [`54507813d40d`](https://github.com/Entif-AI/Bilqis-MLX/commit/54507813d40dcde4128eb20eaf8a40d7380072a9) `docs(test): record independent script import migration debt`
- [`472989acda0a`](https://github.com/Entif-AI/Bilqis-MLX/commit/472989acda0a184b9bc190c12a9ac754599656e3) `refactor(factory): split execution plan ownership without contract changes`
- [`ae3530e1e28a`](https://github.com/Entif-AI/Bilqis-MLX/commit/ae3530e1e28af78584327ca3a57231e76c45a336) `docs(bamf): bound expensive diagnostic loops`
- [`2debce4f4e38`](https://github.com/Entif-AI/Bilqis-MLX/commit/2debce4f4e389c95af295048ff624a54f47c5477) `docs(bamf): gate scope expansion without suppressing decomposition`
- [`a0a00feff659`](https://github.com/Entif-AI/Bilqis-MLX/commit/a0a00feff65915f17063ece7fef2a88ed0ece98a) `fix(factory): retain public class inspection and literal compatibility witnesses`
- [`0ae7c52500ad`](https://github.com/Entif-AI/Bilqis-MLX/commit/0ae7c52500addd4ba08935398529fa8e1a880f31) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/bamf02-a-842-execution-structure-20261105`
- [`6dc77625f8e0`](https://github.com/Entif-AI/Bilqis-MLX/commit/6dc77625f8e0b15f328eacf43681da37cc15b1cf) `docs(bamf): record Factory proof and current unified intake`
- [`edae20526c34`](https://github.com/Entif-AI/Bilqis-MLX/commit/edae20526c34b628fa63a895fb852921007f42a0) `test(runner): enroll package provenance regressions in CI`
- [`fe0939b06838`](https://github.com/Entif-AI/Bilqis-MLX/commit/fe0939b0683882009e97d1fe998a26d02debd53b) `fix(test): import script helpers from canonical owners`
- [`92144d108913`](https://github.com/Entif-AI/Bilqis-MLX/commit/92144d10891381b960535701f05298e84c4f170d) `docs(bamf): record Factory round two pass and held work inventory`
- [`770c89873b88`](https://github.com/Entif-AI/Bilqis-MLX/commit/770c89873b8856ad3ef253ade8fda827d511599b) `fix(bamf): scope extraction proof state and reconcile turn-in inventory`
- [`321315da9ed0`](https://github.com/Entif-AI/Bilqis-MLX/commit/321315da9ed0bcbc8c26814f745e72eef8a385cc) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/bamf02-b-844-script-imports-20261105`
- [`70a4ef1e883d`](https://github.com/Entif-AI/Bilqis-MLX/commit/70a4ef1e883d348920d64083c7546f443a90ef77) `fix(test): preserve native package context for unique file modules`
- [`a5550d348639`](https://github.com/Entif-AI/Bilqis-MLX/commit/a5550d34863989fa258b8f81b61916300f26a868) `docs(test): correct pending review receipt`
- [`b0110a13165c`](https://github.com/Entif-AI/Bilqis-MLX/commit/b0110a13165ccd48670243772cb024c31c5d9660) `chore(bamf): activate selector custody continuation`
- [`815e649aa257`](https://github.com/Entif-AI/Bilqis-MLX/commit/815e649aa25782ce147dac3a56fd7efe963ae1d8) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/bamf02-b-451-selector-custody-20261103`
- [`4f9a7c5aef8e`](https://github.com/Entif-AI/Bilqis-MLX/commit/4f9a7c5aef8e6cfd27a9c8b9abf3d9afe41e612c) `chore(bamf): record reviewed runner and import turn-ins`
- [`acf21b5e20f4`](https://github.com/Entif-AI/Bilqis-MLX/commit/acf21b5e20f4c72874e93739d360cbf0cb491cb3) `chore(bamf): reactivate 842 for conflict resolution`
- [`fce5c63aaa58`](https://github.com/Entif-AI/Bilqis-MLX/commit/fce5c63aaa58402f72460a64a0fe808d5db19a1d) `docs(bamf): record selector custody continuation proof`
- [`1f84411ff632`](https://github.com/Entif-AI/Bilqis-MLX/commit/1f84411ff632ee33cb71cecb44e0787df24c0b31) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/bamf02-b-844-script-imports-20261105`
- [`eead07f2c2b0`](https://github.com/Entif-AI/Bilqis-MLX/commit/eead07f2c2b01cf43e5916bd934b04cfd9c2c9ff) `Merge reviewed unified after PR847`
- [`a0e8466ee4d7`](https://github.com/Entif-AI/Bilqis-MLX/commit/a0e8466ee4d724ac48cb395df5314ec9495a2a62) `docs(test): record combined runner import proof`
- [`0bf808711c82`](https://github.com/Entif-AI/Bilqis-MLX/commit/0bf808711c82a36768ecc383e81e7002149769f7) `chore(bamf): turn in 842 after unified sync`
- [`ebe19aaed0a3`](https://github.com/Entif-AI/Bilqis-MLX/commit/ebe19aaed0a3d345135acc06d6e8a12ffd00ef54) `docs(bamf): clarify selector turn-in and gates`
- [`879c39dd6830`](https://github.com/Entif-AI/Bilqis-MLX/commit/879c39dd68308c7a8e5f8c09bc1624317f47b457) `refactor(bamf): split Factory execution while preserving public contracts`
- [`33a63c11b859`](https://github.com/Entif-AI/Bilqis-MLX/commit/33a63c11b85915a61e9315993fd762a94c3928ce) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/bamf02-b-451-selector-custody-20261103`
- [`57b9ee5721e9`](https://github.com/Entif-AI/Bilqis-MLX/commit/57b9ee5721e99c8d0ab4e4f29b96bd02ab803965) `chore(bamf): reactivate 844 for unified sync`
- [`030880888e09`](https://github.com/Entif-AI/Bilqis-MLX/commit/030880888e09ddbaba98973962af844b9bec7ccc) `Merge reviewed unified after PR846`
- [`5ee8f8fd454f`](https://github.com/Entif-AI/Bilqis-MLX/commit/5ee8f8fd454fe5d38396413683434a86b2408957) `chore(bamf): link selector custody turn-in`
- [`5819d53b3fca`](https://github.com/Entif-AI/Bilqis-MLX/commit/5819d53b3fca59923eee9ee15ff0717bab3bca6f) `chore(bamf): turn in 844 after unified sync`
- [`d29fd6cd290d`](https://github.com/Entif-AI/Bilqis-MLX/commit/d29fd6cd290d88f0b3dbd1557b7ce229db0caab3) `fix(test): restore canonical helper imports in script tests`
- [`c235ebb019b2`](https://github.com/Entif-AI/Bilqis-MLX/commit/c235ebb019b2bf4c71cec77816c5b3987919f853) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/bamf02-b-451-selector-custody-20261103`
- [`77cd6bf9a49d`](https://github.com/Entif-AI/Bilqis-MLX/commit/77cd6bf9a49d947d602797c9f5554971ef555728) `test(bamf): prove selector tensor identity and cold custody`
- [`00858a7f2664`](https://github.com/Entif-AI/Bilqis-MLX/commit/00858a7f26648c0dbdc89cfd567acb2f81787e99) `merge: stack #708 owner on current remediation candidate`
- [`6fe5ae9fb9c7`](https://github.com/Entif-AI/Bilqis-MLX/commit/6fe5ae9fb9c7a5e4c3cb63184f37ff9c3e3eed87) `refactor(bamf): split cognitive DAG authority owner`
- [`9e9f6b364ced`](https://github.com/Entif-AI/Bilqis-MLX/commit/9e9f6b364cedd5ba95fb27796ff45872d034621c) `fix(bamf): bind candidate steps to Factory training authority`
- [`1f1e826c4908`](https://github.com/Entif-AI/Bilqis-MLX/commit/1f1e826c49082ee3c357903f1ac0ff820c1c0742) `fix(bamf): route TaskGoal holes through B10`
- [`a80f24ee724f`](https://github.com/Entif-AI/Bilqis-MLX/commit/a80f24ee724fc482de260ff241a7e7ca53b9ff7f) `fix(bamf): bind C04 task lowering to Factory source authority`
- [`b10d822c3cb3`](https://github.com/Entif-AI/Bilqis-MLX/commit/b10d822c3cb3187c0febfc9d20f5fad68861dafb) `fix(bamf): build Factory-owned C04 evaluation path`
- [`cfca050b0929`](https://github.com/Entif-AI/Bilqis-MLX/commit/cfca050b0929ed808309603bf4a5cb1a9d0ff811) `wip(bamf): checkpoint source-owned C05 retention execution`
- [`fd23f0354f56`](https://github.com/Entif-AI/Bilqis-MLX/commit/fd23f0354f569cb395d92f8df618c20594601d57) `perf(bamf): hash depth-view custody once per receipt validation`
- [`e11e465ef3e6`](https://github.com/Entif-AI/Bilqis-MLX/commit/e11e465ef3e65fd3814b81d6a925248cc47ebd10) `wip(bamf): preserve c05 acceptance diagnosis`
- [`d5a8db8309d8`](https://github.com/Entif-AI/Bilqis-MLX/commit/d5a8db8309d8b7a8c8b15c955639e035ad7e9f05) `test(bamf): preserve cognitive DAG import boundary`
- [`eb91867ae328`](https://github.com/Entif-AI/Bilqis-MLX/commit/eb91867ae328056c9d1b4ca91d88e1f2ea48c547) `fix(bamf): preserve producer-owned receipt graph`
- [`8c2b23c2d0ee`](https://github.com/Entif-AI/Bilqis-MLX/commit/8c2b23c2d0ee57c2a8a2236035c3cb0654e9dc2f) `fix(test): bound cognitive DAG import traversal`
- [`c55e2a69f56f`](https://github.com/Entif-AI/Bilqis-MLX/commit/c55e2a69f56f21176c06d7eb61171ab25a87423d) `fix(bamf): clear C04 C05 operator contract debt`
- [`9d5f12ca39bf`](https://github.com/Entif-AI/Bilqis-MLX/commit/9d5f12ca39bf26d77a1f6fceb650b15f3e853b45) `refactor(bamf): compartmentalize source adapters`
- [`b7559a9ed05b`](https://github.com/Entif-AI/Bilqis-MLX/commit/b7559a9ed05b2edaea211b2510ef3b9aa041cbe9) `fix(quality): honor reviewed base in local premerge gates`
- [`6e12e5a07718`](https://github.com/Entif-AI/Bilqis-MLX/commit/6e12e5a077183713241bb9b2b0d0762d8d95fa47) `fix(quality): honor reviewed base in local premerge gates`
- [`7f3efa7479dd`](https://github.com/Entif-AI/Bilqis-MLX/commit/7f3efa7479ddcb63110fb77615c34ebcce0d39b5) `Merge commit '6e12e5a077183713241bb9b2b0d0762d8d95fa47' into codex/bamf02-b-708-c05-owner-20261105`
- [`887c0c56cf3c`](https://github.com/Entif-AI/Bilqis-MLX/commit/887c0c56cf3c3c1199141a95c82ce2ba4faa0528) `merge: consume reviewed unified after #851`
- [`2359a87b17c5`](https://github.com/Entif-AI/Bilqis-MLX/commit/2359a87b17c5f656838f71b12a172840680df47d) `refactor(bamf): clear 708 premerge structural debt`
- [`8019bf5d945a`](https://github.com/Entif-AI/Bilqis-MLX/commit/8019bf5d945a1d9f8f5a11983ef43fbb008a365f) `Merge reviewed unified into Lane A workstream`
- [`0d6f3c10487d`](https://github.com/Entif-AI/Bilqis-MLX/commit/0d6f3c10487d9207791126f946c498915fa9f3a5) `test(bamf): split atlas frontier snapshot tests`
- [`41662adecbf6`](https://github.com/Entif-AI/Bilqis-MLX/commit/41662adecbf6b4e5bd0e8ac82ff8ef7bb87a94b5) `feat(bamf): wire atlas planner into factory proposal (#395)`
- [`8230403fdae3`](https://github.com/Entif-AI/Bilqis-MLX/commit/8230403fdae3017a89121c4984a741a49d366a8c) `fix(bamf): preserve typed atlas debt and selection authority (#395)`
- [`ad28e099a145`](https://github.com/Entif-AI/Bilqis-MLX/commit/ad28e099a145133ac5e35a3e90a8279fcb201d87) `Merge remote-tracking branch 'origin/codex/bamf02-b-708-c05-owner-20261105' into codex/bamf02-b-708-c05-owner-20261105`
- [`c2e212e0bef7`](https://github.com/Entif-AI/Bilqis-MLX/commit/c2e212e0bef7975e78dfc2f0a6071e21566b6539) `chore(bamf): checkpoint A09.5 realization hold`
- [`888c609cdeb4`](https://github.com/Entif-AI/Bilqis-MLX/commit/888c609cdeb4da9eeb9ca99b7f8bdf087188ca04) `feat(bamf): compile provenance-safe BRAVO evidence lessons (#421)`
- [`c0ccc4db8b20`](https://github.com/Entif-AI/Bilqis-MLX/commit/c0ccc4db8b2069c191c70afc34861a80236f3019) `chore(bamf): turn in A10.1 for review (#421)`
- [`20fc97766b01`](https://github.com/Entif-AI/Bilqis-MLX/commit/20fc97766b01b1f3f737bcf0099e125f9533dc31) `feat(bamf): generate checker-grounded semantic contrasts (#424)`
- [`91d76c053a26`](https://github.com/Entif-AI/Bilqis-MLX/commit/91d76c053a265ca1e7bfae627897f1dfa30b3bef) `chore(bamf): turn in A11.1 for review (#424)`
- [`b3ae176eb93d`](https://github.com/Entif-AI/Bilqis-MLX/commit/b3ae176eb93dc73fffe6f66a4050885fb3f1ca25) `fix(bamf): bind attention caches to model identity`
- [`028a5c0d594a`](https://github.com/Entif-AI/Bilqis-MLX/commit/028a5c0d594a71724a47d2b0928fa8236b6cf87f) `chore(bamf): track 754 cache transition`
- [`00c31b06d15a`](https://github.com/Entif-AI/Bilqis-MLX/commit/00c31b06d15aa759fb94f7d51b1500da7c15b455) `test(bamf): prove accepted cache transition`
- [`27007685b160`](https://github.com/Entif-AI/Bilqis-MLX/commit/27007685b1600685a978f2338dfc6a0dbcb184e4) `chore(bamf): refresh 754 transition receipt`
- [`75185447763a`](https://github.com/Entif-AI/Bilqis-MLX/commit/75185447763a34d7c2154965b07f832b681babe2) `test(bamf): restore frozen v1 cache witness`
- [`f247a05adf19`](https://github.com/Entif-AI/Bilqis-MLX/commit/f247a05adf190662450ab48c75cbbc63c99a2499) `chore(bamf): record 754 frozen witness`
- [`470669883bdc`](https://github.com/Entif-AI/Bilqis-MLX/commit/470669883bdc624d892a2e2e64d610555c81d936) `chore(bamf): activate 719 cache authority`
- [`0343b3ae8c4b`](https://github.com/Entif-AI/Bilqis-MLX/commit/0343b3ae8c4b766b63fa2b20315d2d9f7d7cd82d) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/719-cache-eligibility-authority-20261105`
- [`c2983e872191`](https://github.com/Entif-AI/Bilqis-MLX/commit/c2983e872191fea98a369ad553447c20aff28af7) `Fix A10.1 opaque numeric guard contract`
- [`7c976dff2ec0`](https://github.com/Entif-AI/Bilqis-MLX/commit/7c976dff2ec060624a310a364eb33abb64d18f6d) `Refactor A11.1 contrast type contracts`
- [`bba77c0651fd`](https://github.com/Entif-AI/Bilqis-MLX/commit/bba77c0651fd06e692f7b9b4eeb971f987005d86) `Refactor A11.1 contrast artifact models`
- [`23d1ea64bb61`](https://github.com/Entif-AI/Bilqis-MLX/commit/23d1ea64bb61ac29431f2a1405cb30ff03e3e931) `Refactor A11.1 contrast transformations`
- [`4e0127836444`](https://github.com/Entif-AI/Bilqis-MLX/commit/4e0127836444c648cdc4c95e3fb9f3d88df37f93) `Refactor A11.1 contrast checker`
- [`be8bab2866e3`](https://github.com/Entif-AI/Bilqis-MLX/commit/be8bab2866e3212cae41d401bff03cfee7a7a36f) `Refactor A11.1 semantic contrasts under module-size gate`
- [`3a96c9056d5e`](https://github.com/Entif-AI/Bilqis-MLX/commit/3a96c9056d5e821f0376962bdd15788dc86a442e) `Repair A10.1 named duration arity constant`
- [`482266855e57`](https://github.com/Entif-AI/Bilqis-MLX/commit/482266855e57c74352a5542fc57d000e1c589117) `Remove opaque A11.1 unreachable error literals`
- [`cd45d3aeda8e`](https://github.com/Entif-AI/Bilqis-MLX/commit/cd45d3aeda8ebf01d90ddaceeba33be1e544ff1d) `Refactor A11.1 variation validation dispatch`
- [`f23eee291ca8`](https://github.com/Entif-AI/Bilqis-MLX/commit/f23eee291ca8c1745a8a2843a88690830803e09c) `Refactor A11.1 contrast transform dispatch`
- [`5350df114a02`](https://github.com/Entif-AI/Bilqis-MLX/commit/5350df114a02c457d3afeb56145835e1f9002c43) `Freeze A11.1 _VARIATION_VALIDATORS dispatch table`
- [`5a1d4a2d3b2e`](https://github.com/Entif-AI/Bilqis-MLX/commit/5a1d4a2d3b2ebb290b044925c86aa89d00f9b67c) `Freeze A11.1 _TRANSFORMS dispatch table`
- [`f81f0d8648fe`](https://github.com/Entif-AI/Bilqis-MLX/commit/f81f0d8648fe0a73865fc78c92f0eb795560f83a) `Repair frozen A11.1 dispatch syntax`
- [`3c5bf4d4571c`](https://github.com/Entif-AI/Bilqis-MLX/commit/3c5bf4d4571cca8a020ba8bbcf5609fcdd0261e4) `Repair frozen A11.1 dispatch syntax`
- [`2c3f2e2cf413`](https://github.com/Entif-AI/Bilqis-MLX/commit/2c3f2e2cf413c084ae814f96813c2e19615c0221) `fix(bamf): bind cache eligibility to accepted authority`
- [`207c61c0934b`](https://github.com/Entif-AI/Bilqis-MLX/commit/207c61c0934b5ae464c10dc14aa01ddd19adcb9e) `refactor(bamf): isolate cache authority derivation`
- [`046d0ee446c0`](https://github.com/Entif-AI/Bilqis-MLX/commit/046d0ee446c02d5a2f2e3c00768f41a375b5c5aa) `chore(bamf): record 719 authority repair`
- [`9758299ef0be`](https://github.com/Entif-AI/Bilqis-MLX/commit/9758299ef0beab9592c10b3cffc32d115d1733a0) `chore(bamf): bind 719 to PR 854`
- [`8edb4084b0f1`](https://github.com/Entif-AI/Bilqis-MLX/commit/8edb4084b0f181a87f11171cfea5095f958a2c2a) `chore(bamf): park 719 on pinned EGM`
- [`16ff7f3696f1`](https://github.com/Entif-AI/Bilqis-MLX/commit/16ff7f3696f11990b860de8eaad09a9a08080cdc) `chore(bamf): keep open 719 PR active`
- [`0341232765ed`](https://github.com/Entif-AI/Bilqis-MLX/commit/0341232765ed10a4d134b2c79ac28105671557e1) `fix(bamf): restore exact lane-b issue states`
- [`046cb64f180a`](https://github.com/Entif-AI/Bilqis-MLX/commit/046cb64f180af1b1b73098d0d4e025f05ad2548b) `feat(bamf): compile provenance-safe BRAVO evidence lessons (A10.1)`
- [`ea080d455fe8`](https://github.com/Entif-AI/Bilqis-MLX/commit/ea080d455fe8d3c107059414626e98ff0b130491) `Merge remote-tracking branch 'origin/codex/bamf02-a10-1-421-20261105' into codex/bamf02-a10-2-422-20261105`
- [`2fe7188f8bab`](https://github.com/Entif-AI/Bilqis-MLX/commit/2fe7188f8bab67460dda90ba4a6442cefa98c06c) `Merge remote-tracking branch 'origin/pr-852-head' into codex/bamf02-a10-2-422-20261105`
- [`ce44d97a60af`](https://github.com/Entif-AI/Bilqis-MLX/commit/ce44d97a60af578054eecdfe0c40b2a0a5ba9e0f) `Merge reviewed unified into A11.1 and resolve Lane A flow control`
- [`202dbb313b36`](https://github.com/Entif-AI/Bilqis-MLX/commit/202dbb313b3681c2730974da8c2ee93acb8fb738) `feat(bamf): compile typed BRAVO reconstructions (#422)`
- [`e2fa1d782d36`](https://github.com/Entif-AI/Bilqis-MLX/commit/e2fa1d782d3631c65d9915f0fa57c75644741bf8) `chore(bamf): turn in A10.2 for review (#422)`
- [`67cb162104fc`](https://github.com/Entif-AI/Bilqis-MLX/commit/67cb162104fca25afb6003b36493f583de600194) `Refactor A11.1 implementation into semantic_contrast package`
- [`29b95d86a477`](https://github.com/Entif-AI/Bilqis-MLX/commit/29b95d86a477a678e32d4928d639eba1b1cecd99) `Merge remote-tracking branch 'origin/pr-853-head' into codex/bamf02-a11-2-425-20261105`
- [`c6336800a803`](https://github.com/Entif-AI/Bilqis-MLX/commit/c6336800a803fb11b1b3602c0f5f0dcc2348c8b4) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/bamf02-a10-2-422-20261105`
- [`90adf0371e5d`](https://github.com/Entif-AI/Bilqis-MLX/commit/90adf0371e5d63c17f6aa674d9d2ac78db67bdcc) `chore(bamf): reconcile A10.2 after A10.1 merge (#422)`
- [`eedfdaef9f52`](https://github.com/Entif-AI/Bilqis-MLX/commit/eedfdaef9f528c02618963c8486ade4d12fcb18f) `feat(bamf): generate checker-grounded structural contrasts (A11.1)`
- [`3fa3e439c490`](https://github.com/Entif-AI/Bilqis-MLX/commit/3fa3e439c490294d905a537919b5da4dc746bc29) `chore(bamf): register A10.2 PR #855`
- [`5f87f6ae7504`](https://github.com/Entif-AI/Bilqis-MLX/commit/5f87f6ae750475298b6c732282843b8b7ce5a470) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/bamf02-a10-2-422-20261105`
- [`0c82a3ba4e36`](https://github.com/Entif-AI/Bilqis-MLX/commit/0c82a3ba4e36b1acfc91e1b753ffea8133e2bca3) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/bamf02-a11-2-425-20261105`
- [`04b7ad862235`](https://github.com/Entif-AI/Bilqis-MLX/commit/04b7ad8622355273410cb38cb141bb5689e3ee73) `fix(bamf): restore A11.1 SHA validation (#424)`
- [`db13fad17d10`](https://github.com/Entif-AI/Bilqis-MLX/commit/db13fad17d108bc4c09cf6447436edbb774ddf19) `Merge remote-tracking branch 'origin/pr-856-head' into codex/bamf02-a11-2-425-20261105`
- [`ad7374138e71`](https://github.com/Entif-AI/Bilqis-MLX/commit/ad7374138e718e77df62933e16ee36bbf1d59346) `feat(bamf): bound ambiguity and noise lineage (#425)`
- [`ca98b1749f53`](https://github.com/Entif-AI/Bilqis-MLX/commit/ca98b1749f5387a38a4d5ed4bd3d70f11c81eb8a) `chore(bamf): turn in A11.2 for review (#425)`
- [`e09eaa323bfb`](https://github.com/Entif-AI/Bilqis-MLX/commit/e09eaa323bfbb8abaef2e3fc3899e66d872ad97b) `feat(bamf): compile typed BRAVO reconstructions (A10.2)`
- [`2cb50e3a9319`](https://github.com/Entif-AI/Bilqis-MLX/commit/2cb50e3a9319552ca847ba69ad8b2beeb03cf194) `fix(bamf): restore A11.1 SHA validation`
- [`c44577d2c64d`](https://github.com/Entif-AI/Bilqis-MLX/commit/c44577d2c64d85a97bdfe0bf12d07d286dac4a89) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/bamf02-a11-2-425-20261105`
- [`098e1ebeec2f`](https://github.com/Entif-AI/Bilqis-MLX/commit/098e1ebeec2ffa4a6cd050847523ed6b045fb119) `fix(bamf): name A11.2 digest length contract (#425)`
- [`e27760306dfb`](https://github.com/Entif-AI/Bilqis-MLX/commit/e27760306dfb17d1b5ba316b5809fb1784d6cdf7) `feat(bamf): bind literal public BRAVO fixture receipt (#423)`
- [`42a00888811a`](https://github.com/Entif-AI/Bilqis-MLX/commit/42a00888811a7a84b473e54773a416e43e49cdc8) `fix(bamf): name public fixture gold contracts (#423)`
- [`243d9130a5e5`](https://github.com/Entif-AI/Bilqis-MLX/commit/243d9130a5e57a21959bc13373ef6dbbcb436622) `chore(bamf): turn in A10.3 for review (#423)`
- [`85a64cd41847`](https://github.com/Entif-AI/Bilqis-MLX/commit/85a64cd41847a04143cb1ef0e5d5c11bfc970c8d) `chore(bamf): register A10.3 PR #858`
- [`4df4d1b0cba1`](https://github.com/Entif-AI/Bilqis-MLX/commit/4df4d1b0cba1bb02d5d52155298e2b85bc640b37) `fix(bamf): preserve evidence family and unit authority`
- [`88ac132db2fd`](https://github.com/Entif-AI/Bilqis-MLX/commit/88ac132db2fd1c3606fa5f06637d10a7ab40cba4) `feat(bamf): bound ambiguity and noise lineage (A11.2)`
- [`b965f3d77e17`](https://github.com/Entif-AI/Bilqis-MLX/commit/b965f3d77e17ead8a46b210093b8aed3a3abb6c6) `fix(bamf): harden A10.3 witness independence (#423)`
- [`2bc2d436e42f`](https://github.com/Entif-AI/Bilqis-MLX/commit/2bc2d436e42fed52a69073cacb6d845e781957b3) `fix(bamf): publish BRAVO evidence frame schema`
- [`6c37819aa696`](https://github.com/Entif-AI/Bilqis-MLX/commit/6c37819aa6968326c3cefd470f39dcd226cc91ec) `chore(bamf): record A10.3 review hardening (#423)`
- [`e062c56c2e66`](https://github.com/Entif-AI/Bilqis-MLX/commit/e062c56c2e66df3dcab6ed18fcae6bac7620d71a) `fix(bamf): make public BRAVO gold fixture immutable`
- [`cac73477f6cc`](https://github.com/Entif-AI/Bilqis-MLX/commit/cac73477f6ccf6c3b5bae8539521c1920b7e36aa) `Merge remote-tracking branch 'origin/codex/bamf02-a-semantics' into codex/bamf02-a-578-evidence-schema-20261105`
- [`76f144c9690d`](https://github.com/Entif-AI/Bilqis-MLX/commit/76f144c9690de21d550f0dbf0a7af8905c0f655f) `fix(bamf): bind cache eligibility to owner state`
- [`0f43e049627a`](https://github.com/Entif-AI/Bilqis-MLX/commit/0f43e049627a5f02eefea2da1abbad2bb792ac54) `feat(bamf): connect semantic contrasts to Factory teacher (#426)`
- [`59f45809b1c8`](https://github.com/Entif-AI/Bilqis-MLX/commit/59f45809b1c8b23d9ace4f5cb1f1a0870d53b37b) `docs(bamf): record cache authority repair`
- [`50f0ffc09d2b`](https://github.com/Entif-AI/Bilqis-MLX/commit/50f0ffc09d2b11fc66e36dc3c4fd3f276755ecc2) `chore(bamf): turn in A11.3 and reconcile Lane A`
- [`aa9693c149f3`](https://github.com/Entif-AI/Bilqis-MLX/commit/aa9693c149f366e14d3e7e76fb6db2dc25c17dc9) `fix(bamf): unify A03 schema pin generator`
- [`7c51038b6da5`](https://github.com/Entif-AI/Bilqis-MLX/commit/7c51038b6da5a8644531feec01cf7dc58891b72f) `chore(bamf): merge current unified into A10.3 candidate`
- [`def3b35dc7b7`](https://github.com/Entif-AI/Bilqis-MLX/commit/def3b35dc7b700988695b184e7b42a45722b0a24) `fix(bamf): record A10.3 waiting-PR exception`
- [`c5c3ce914d4b`](https://github.com/Entif-AI/Bilqis-MLX/commit/c5c3ce914d4bdcc2366bae207ce2aa572f6a933b) `docs(bamf): name evidence family in A03 generator`
- [`c59bdf041198`](https://github.com/Entif-AI/Bilqis-MLX/commit/c59bdf041198107b0cd03b12f5662dbab0f30e1f) `refactor(bamf): compartmentalize public BRAVO fixture owner`
- [`0d02016a8c52`](https://github.com/Entif-AI/Bilqis-MLX/commit/0d02016a8c5295364db491b7a55d27dc83b46252) `fix(bamf): publish bindable BRAVO agent role`
- [`38e41d521ade`](https://github.com/Entif-AI/Bilqis-MLX/commit/38e41d521ade59d283a1c9547b18efe5927e8019) `fix(bamf): bind A11.3 to event-frame source owner (#426)`
- [`28a4a1befd29`](https://github.com/Entif-AI/Bilqis-MLX/commit/28a4a1befd2915f37e5cff991b9b8f9afe42c61f) `chore(bamf): record A11.3 real-owner repair (#426)`
- [`8fa2f6128cde`](https://github.com/Entif-AI/Bilqis-MLX/commit/8fa2f6128cde1b3e3c62d4b070a142c1c7b6907f) `chore(bamf): register A11.3 PR #860`
- [`173f3751ea7e`](https://github.com/Entif-AI/Bilqis-MLX/commit/173f3751ea7e60e1cf4141e8e761363664ef1b64) `test(bamf): split released pin witnesses`
- [`35e547c807f3`](https://github.com/Entif-AI/Bilqis-MLX/commit/35e547c807f30122db2c2ed92e46b8a3d0ab33f0) `refactor(bamf): compartmentalize semantic contrast tests (#426)`
- [`3e173b1c2d44`](https://github.com/Entif-AI/Bilqis-MLX/commit/3e173b1c2d44fe37ff3f9fed5037600722dfe0e6) `fix(bamf): enforce current cache authority at use`
- [`926b6debd43d`](https://github.com/Entif-AI/Bilqis-MLX/commit/926b6debd43d7ff7391d56eff84703ca119de4de) `docs(bamf): record cache currentness repair`
- [`9180b0a8157a`](https://github.com/Entif-AI/Bilqis-MLX/commit/9180b0a8157a9478499f02787dbdce314ad99374) `fix(bamf): bind contrast teaching to provider identity`
- [`978ac9273816`](https://github.com/Entif-AI/Bilqis-MLX/commit/978ac92738169f1e2e2be0751701900a937e3fdd) `feat(bamf): publish source-pinned BRAVO AGENT role (A03.4)`
- [`22314c413ba1`](https://github.com/Entif-AI/Bilqis-MLX/commit/22314c413ba137df69b3d6b35768fe65e1556bfe) `feat(bamf): connect source-valid contrasts to Factory teacher (A11.3)`
- [`68f288cd9e20`](https://github.com/Entif-AI/Bilqis-MLX/commit/68f288cd9e20b54bbc8c0b8a775196b9f3335ba8) `feat(bamf): audit atlas authority consumers`
- [`65fa054ed312`](https://github.com/Entif-AI/Bilqis-MLX/commit/65fa054ed312ffe7485516d8fb564d188d7220c1) `docs(bamf): record A12.1 authority audit receipt`
- [`6bf96065f01d`](https://github.com/Entif-AI/Bilqis-MLX/commit/6bf96065f01d1cb2c24bcc9a02065ab0476d99f8) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/bamf02-a12-1-427-20261105`
- [`61a177aabc4f`](https://github.com/Entif-AI/Bilqis-MLX/commit/61a177aabc4fd8038100bcb305cda4fa552b8403) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/bamf02-a-421-egm-repair-20261105`
- [`94193f51451a`](https://github.com/Entif-AI/Bilqis-MLX/commit/94193f51451ad8216beb4b62a6fec79c07796a4c) `fix(bamf): bind evidence to admitted semantics`
- [`fd39db9a59d2`](https://github.com/Entif-AI/Bilqis-MLX/commit/fd39db9a59d218fcc88c89f62ee66f501c5d8a04) `docs(bamf): checkpoint A10.1 EGM repair`
- [`ad4e2739e16e`](https://github.com/Entif-AI/Bilqis-MLX/commit/ad4e2739e16eec9ab637ffa63c0416f5e58186ce) `chore(bamf): register A10.1 repair PR`
- [`2a314e44d955`](https://github.com/Entif-AI/Bilqis-MLX/commit/2a314e44d955881588d89af0f3a5efc5ddc6a9a9) `fix(bamf): bind A12 prior ABI authority`
- [`2223c1ab3439`](https://github.com/Entif-AI/Bilqis-MLX/commit/2223c1ab3439e86bcc4a76b8d156209995a14c79) `fix(bamf): close A10.1 EGM authority gaps`
- [`b00309858764`](https://github.com/Entif-AI/Bilqis-MLX/commit/b003098587642987045813c69d4d733abf651089) `fix(bamf): bind evidence families to source episode roots`
- [`2a9fe4e9d5b9`](https://github.com/Entif-AI/Bilqis-MLX/commit/2a9fe4e9d5b91a37f7bb868d1b483dc4ebff6dcc) `docs(bamf): refresh A10.1 repair custody`
- [`e1753a5b8013`](https://github.com/Entif-AI/Bilqis-MLX/commit/e1753a5b8013d4a6b346d87179280de110f39580) `fix(bamf): derive evidence roots from source provenance`
- [`9ff227c012ed`](https://github.com/Entif-AI/Bilqis-MLX/commit/9ff227c012ede5573257b6aeac73f31c636c5f18) `docs(bamf): record provenance-root repair`
- [`26e32982dc06`](https://github.com/Entif-AI/Bilqis-MLX/commit/26e32982dc068014819aeedbac7f335900f6de9b) `fix(bamf): make evidence checker independent`
- [`912f2fc739eb`](https://github.com/Entif-AI/Bilqis-MLX/commit/912f2fc739eb4c9808e31cc14d9a60f338a7200c) `fix(bamf): bind evidence families to source manifests`
- [`01f3c168be85`](https://github.com/Entif-AI/Bilqis-MLX/commit/01f3c168be85c5dd27e54e003aae051ab4e42b28) `docs(bamf): record source-family manifest repair`
- [`e44a95a35a19`](https://github.com/Entif-AI/Bilqis-MLX/commit/e44a95a35a196399b086b293bcdc82fa816527a5) `Merge remote-tracking branch 'origin/codex/bamf02-a-421-egm-repair-20261105' into codex/bamf02-a-421-egm-repair-20261105`
- [`b08628b596cf`](https://github.com/Entif-AI/Bilqis-MLX/commit/b08628b596cf31fde804fe4711139caaf6ad4652) `fix(bamf): preserve exact evidence conversion`
- [`ea8127d89c89`](https://github.com/Entif-AI/Bilqis-MLX/commit/ea8127d89c8996530dac96732fb162e22252f8bc) `docs(bamf): reconcile A10.1 combined repair custody`
- [`382df799e0a6`](https://github.com/Entif-AI/Bilqis-MLX/commit/382df799e0a6e15dad8ddfd1a5632ef81490a593) `Merge remote-tracking branch 'origin/codex/bamf02-a-421-egm-repair-20261105' into codex/bamf02-a-421-egm-repair-20261105`
- [`4530b101ee27`](https://github.com/Entif-AI/Bilqis-MLX/commit/4530b101ee27774acf9ee00aec6b6d76f96cb10d) `fix(bamf): name exact decimal factors`
- [`a044613f5bc4`](https://github.com/Entif-AI/Bilqis-MLX/commit/a044613f5bc4c00eede2b8d5fef3a28f3e7579a5) `Merge remote-tracking branch 'origin/codex/bamf02-a-421-egm-repair-20261105' into codex/bamf02-a-421-egm-repair-20261105`
- [`33117d1edb7b`](https://github.com/Entif-AI/Bilqis-MLX/commit/33117d1edb7b30d0da930c10db7cf548a88cc635) `docs(bamf): finalize A10.1 combined repair receipt`
- [`8d76814e137a`](https://github.com/Entif-AI/Bilqis-MLX/commit/8d76814e137a724dc0a761f7f53967dbb40b538a) `fix(bamf): align foundation retention and detached witnesses`
- [`28517f32c036`](https://github.com/Entif-AI/Bilqis-MLX/commit/28517f32c036f6cb55d742b6276811f3d85fdd7f) `refactor(bamf): split evidence adapter contracts`
- [`ae6a824da242`](https://github.com/Entif-AI/Bilqis-MLX/commit/ae6a824da242732b6d6c289b25131b7d28f3b43c) `docs(bamf): record final A10.1 structural repair`
- [`1573038d1b9e`](https://github.com/Entif-AI/Bilqis-MLX/commit/1573038d1b9ee8e618626274fac3e78724bc98a5) `refactor(bamf): split atlas authority audit validation`
- [`859dd3fc3ff9`](https://github.com/Entif-AI/Bilqis-MLX/commit/859dd3fc3ff92bd764b5b39f64e201a50adbd962) `docs(bamf): refresh A12.1 turn-in custody`
- [`e808d02737db`](https://github.com/Entif-AI/Bilqis-MLX/commit/e808d02737db2d4dcaa9e3d1c9028f961d792a34) `fix(bamf): make foundation retention fixed-school only`
- [`e929ed2309ca`](https://github.com/Entif-AI/Bilqis-MLX/commit/e929ed2309cad20504a5abadc9d739f66777d5e7) `fix(bamf): close A12 authority audit gaps`
- [`c7be50b5c359`](https://github.com/Entif-AI/Bilqis-MLX/commit/c7be50b5c359a2891b8624f9e57ea717391558b9) `test(bamf): probe non-destructive foundation step`
- [`d6f6206c6408`](https://github.com/Entif-AI/Bilqis-MLX/commit/d6f6206c64089a57ced809706821ce56a4eb2b71) `test(bamf): validate optimizer delta attribution`
- [`defb157478cb`](https://github.com/Entif-AI/Bilqis-MLX/commit/defb157478cbd71b883ee0e7e265ebdd06f60b05) `refactor(bamf): split A12 authority audit tests`
- [`384d09a4c900`](https://github.com/Entif-AI/Bilqis-MLX/commit/384d09a4c9009206ddd7175cde025cbc8ac42972) `refactor(bamf): split held-source audit assertions`
- [`63c8a67d4055`](https://github.com/Entif-AI/Bilqis-MLX/commit/63c8a67d4055e4d6b00d9b1fc79024ed5dd24630) `fix(bamf): replay A12 semantic authority`
- [`38455ba1d27c`](https://github.com/Entif-AI/Bilqis-MLX/commit/38455ba1d27c90c23bb5a1e4aa5967356d7e805e) `Merge remote-tracking branch 'origin/codex/bamf02-a12-1-427-20261105' into codex/pr861-held-gloss-repair`
- [`c5b94d6196dc`](https://github.com/Entif-AI/Bilqis-MLX/commit/c5b94d6196dc2de44b68c88500dd82d85a2f0a81) `test(bamf): drop superseded A12 split witness`
- [`99277203ea35`](https://github.com/Entif-AI/Bilqis-MLX/commit/99277203ea3511d68e3cac0aacf0f28769530885) `test(bamf): factor held-source adversary`
- [`a0c0a6b1ced4`](https://github.com/Entif-AI/Bilqis-MLX/commit/a0c0a6b1ced4767b4080c6b24fc0a94e830a4f90) `docs(bamf): refresh A12.1 repair custody`
- [`c0b9c57c7a51`](https://github.com/Entif-AI/Bilqis-MLX/commit/c0b9c57c7a51ef2b96f681ec5fdb09aae314a3cd) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/bamf02-b-708-c05-owner-20261105`
- [`09e30ae5d582`](https://github.com/Entif-AI/Bilqis-MLX/commit/09e30ae5d5829982883b430b745a62e1c1926d4b) `fix(bamf): preserve A10 evidence compiler contract`
- [`c1f3c5b76b28`](https://github.com/Entif-AI/Bilqis-MLX/commit/c1f3c5b76b281df67a8369259bb28976dfd1aea2) `feat(bamf): bind cache eligibility to accepted B13/A12 authority (B14.4)`
- [`f82cda87d044`](https://github.com/Entif-AI/Bilqis-MLX/commit/f82cda87d044871c7bbff1026376400b5c37cea8) `fix(bamf): authenticate A12 export clearance`
- [`a5b73bd5be23`](https://github.com/Entif-AI/Bilqis-MLX/commit/a5b73bd5be2318e4d2a7889ed604321ac425f8c7) `docs(bamf): refresh A12.1 review repair custody`
- [`4fa82bbf6861`](https://github.com/Entif-AI/Bilqis-MLX/commit/4fa82bbf686183ac2071f2ce44805deb189ea3a9) `fix(bamf): preserve accepted A10 public snapshots`
- [`672f97d7049d`](https://github.com/Entif-AI/Bilqis-MLX/commit/672f97d7049dd951f86630844e3a80b60c4563dd) `Merge pull request #862 from Entif-AI/codex/bamf02-a-421-egm-repair-20261105`
- [`73bd28ebdd79`](https://github.com/Entif-AI/Bilqis-MLX/commit/73bd28ebdd7904446163e3b54f17cfb2c16a3546) `Merge reviewed unified after A10.1 acceptance`
- [`c2a3c9e27f98`](https://github.com/Entif-AI/Bilqis-MLX/commit/c2a3c9e27f98f38c4e904bd9bd7d4a05002b3739) `fix(bamf): preserve A12 held-source evidence`
- [`8cae9b082a3a`](https://github.com/Entif-AI/Bilqis-MLX/commit/8cae9b082a3aa72fd8dadabc4439764593f17165) `docs(bamf): record final A12.1 authority proof`
- [`a2ec67b5046a`](https://github.com/Entif-AI/Bilqis-MLX/commit/a2ec67b5046afd9c86add46c7bd5f1483550e61c) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/pr858-mergeability-repair`
- [`7a4dae00fb1e`](https://github.com/Entif-AI/Bilqis-MLX/commit/7a4dae00fb1e927231ec228252bb641199a58ce3) `test(bamf): separate learning witness from provenance gate`
- [`bfad4ccfd356`](https://github.com/Entif-AI/Bilqis-MLX/commit/bfad4ccfd35660b2026eaee8b3caafec4bb4eea5) `fix(bamf): rebind A10.3 fixture to accepted source authority`
- [`23de64b6fc8d`](https://github.com/Entif-AI/Bilqis-MLX/commit/23de64b6fc8d8697344fb60890d616cb0370999e) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/pr861-held-gloss-repair`
- [`f14f8f4f7323`](https://github.com/Entif-AI/Bilqis-MLX/commit/f14f8f4f732306ed17130556951c907dfd5e1085) `docs(bamf): resume A10.3 after accepted A10.1 repair`
- [`9f9afb822415`](https://github.com/Entif-AI/Bilqis-MLX/commit/9f9afb8224154cb381ea0069d2124a57d55f09c7) `fix(bamf): make A10.3 external witnesses replayable`
- [`da8daf6f2cfd`](https://github.com/Entif-AI/Bilqis-MLX/commit/da8daf6f2cfde940bf6b129179ef48283f960b60) `Merge concurrent A10.3 custody repair`
- [`e9fa36a009da`](https://github.com/Entif-AI/Bilqis-MLX/commit/e9fa36a009daf65e5b19a52351993eb2e7d4e242) `fix(bamf): preserve A10.3 witness rights lineage`
- [`4fc284a23314`](https://github.com/Entif-AI/Bilqis-MLX/commit/4fc284a23314a713267429e2afd85b5dcc859c16) `fix(bamf): close A10.3 rights lifecycle gaps`
- [`854c9262022c`](https://github.com/Entif-AI/Bilqis-MLX/commit/854c9262022c6399b821216d2c7243715ffd2f97) `test(bamf): prove A12 deterministic regeneration`
- [`e8f53fe1ebd3`](https://github.com/Entif-AI/Bilqis-MLX/commit/e8f53fe1ebd3281ecaec1711d9b6afef7f330b53) `Merge remote-tracking branch 'origin/codex/bamf02-a10-3-423-20261105' into codex/pr858-final-review`
- [`1599a67b4ac4`](https://github.com/Entif-AI/Bilqis-MLX/commit/1599a67b4ac481c796e26fa302db829db3910e00) `Merge pull request #858 from Entif-AI/codex/bamf02-a10-3-423-20261105`
- [`40912a41c087`](https://github.com/Entif-AI/Bilqis-MLX/commit/40912a41c087282e0147aac00491e0a92d5ff9e1) `test(bamf): align A10.3 rights tamper boundary`
- [`dce1f6a46e22`](https://github.com/Entif-AI/Bilqis-MLX/commit/dce1f6a46e22c919746d03574c76654e85f57055) `Merge reviewed unified after A10 acceptance`
- [`d480e633bce2`](https://github.com/Entif-AI/Bilqis-MLX/commit/d480e633bce2697ac31995c658c650ffa317baca) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/pr861-final-mergeability`
- [`8211a6a024f7`](https://github.com/Entif-AI/Bilqis-MLX/commit/8211a6a024f75aded96158cb5e3b437df0f804a0) `Merge concurrent A12 final mergeability reconciliation`
- [`16f9fb673b37`](https://github.com/Entif-AI/Bilqis-MLX/commit/16f9fb673b377d561ecbffd820e09b3c30de8f3c) `docs(bamf): preserve merged A10 authority in A12 custody`
- [`beb699ad7f13`](https://github.com/Entif-AI/Bilqis-MLX/commit/beb699ad7f131bd97a0983c3f27f8a53f7a240cc) `feat(bamf): audit current semantic authority consumers (A12.1)`
- [`70c49117ae99`](https://github.com/Entif-AI/Bilqis-MLX/commit/70c49117ae992e2357b7a81f90eb014655e9f8f3) `fix(bamf): preserve private evidence lineage through trainer prep`
- [`d7b1c6d2850e`](https://github.com/Entif-AI/Bilqis-MLX/commit/d7b1c6d2850eff600965006e7739ed2151c4a78a) `docs(bamf): reconcile A12.1 post-merge custody`
- [`81082507421f`](https://github.com/Entif-AI/Bilqis-MLX/commit/81082507421fdb50d9ae6fb70b00acaf83b25762) `fix(a06): derive feature selection from released source adapters`
- [`a5571154d652`](https://github.com/Entif-AI/Bilqis-MLX/commit/a5571154d6521f6e04050f0310872d14bca8d11f) `test(a06): reject source-valid alternate feature profile`
- [`57ca51c8fb6b`](https://github.com/Entif-AI/Bilqis-MLX/commit/57ca51c8fb6bac68944472dad7971ecd7a89dbc0) `docs(bamf): classify A12 custody PR as non-implementation`
- [`6e2152c14603`](https://github.com/Entif-AI/Bilqis-MLX/commit/6e2152c146037136449ac4559e0153deb30c8990) `fix(a06): avoid semantic import cycle`
- [`f131a51e229b`](https://github.com/Entif-AI/Bilqis-MLX/commit/f131a51e229be0a3a7c3fe057d35dc7523502493) `Merge pull request #867 from Entif-AI/codex/bamf02-a-785-source-authority-20261105`
- [`d47a213596b8`](https://github.com/Entif-AI/Bilqis-MLX/commit/d47a213596b8486fa2b1a5e82100c48bd89cd99e) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/bamf02-b-708-c05-owner-20261105`
- [`c48d5029c9c8`](https://github.com/Entif-AI/Bilqis-MLX/commit/c48d5029c9c8d1d2738ceff734bf32dae06e3cd1) `docs(bamf): record reopened A10.3 remediation custody`
- [`7bcc0be44137`](https://github.com/Entif-AI/Bilqis-MLX/commit/7bcc0be44137d1402dcb53fef0877f96e18ef7a8) `Merge pull request #866 from Entif-AI/codex/bamf02-a12-1-427-postmerge-custody-20261105`
- [`f4d296931141`](https://github.com/Entif-AI/Bilqis-MLX/commit/f4d296931141d0cd32c596edc82ce29e6e887f08) `fix(bamf): bind private evidence source and split custody`
- [`50ff4bf16260`](https://github.com/Entif-AI/Bilqis-MLX/commit/50ff4bf16260da5f594564475bb9ef64024e821a) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/bamf02-a10-3-423-20261105`
- [`3f15216b3aca`](https://github.com/Entif-AI/Bilqis-MLX/commit/3f15216b3acaa1e1345b24c54205918ee8d06783) `refactor(bamf): satisfy source adapter structure gate`
- [`e836f90925cf`](https://github.com/Entif-AI/Bilqis-MLX/commit/e836f90925cfe1b94cbb638aa25933cc2fe70ab1) `Merge pull request #865 from Entif-AI/codex/bamf02-a10-3-423-20261105`
- [`90a1212534c3`](https://github.com/Entif-AI/Bilqis-MLX/commit/90a1212534c3b4e7c30182ffc10541de6a9a5fe9) `docs(bamf): reconcile A10.3 post-merge custody`
- [`fc09bec8de92`](https://github.com/Entif-AI/Bilqis-MLX/commit/fc09bec8de92361f678cac3ed27da0622b35f1bb) `docs(bamf): classify PR 868 as custody-only`
- [`e06cc38eba19`](https://github.com/Entif-AI/Bilqis-MLX/commit/e06cc38eba198509b76836a08b0973a9aa6bc75e) `docs(bamf): refresh Lane A custody frontier`
- [`7c8974191f5c`](https://github.com/Entif-AI/Bilqis-MLX/commit/7c8974191f5c9c5449f1056149776771ad2b72f3) `Merge pull request #868 from Entif-AI/codex/bamf02-a10-3-423-postmerge-custody-20261105`
- [`a9662001f84a`](https://github.com/Entif-AI/Bilqis-MLX/commit/a9662001f84aa61fcfedfc2c91ca68c314001a21) `refactor(bamf): cut current Atlas alias imports`
- [`e6646edd6d29`](https://github.com/Entif-AI/Bilqis-MLX/commit/e6646edd6d299e5de72d2d30371c85743e2b84fd) `docs(bamf): record A12.2 semantic cutover receipt`
- [`a253d579584a`](https://github.com/Entif-AI/Bilqis-MLX/commit/a253d579584adf6ef45c8cedf5e2be3f553d7d29) `docs(bamf): turn in A12.2 candidate`
- [`3b0c1775e0d5`](https://github.com/Entif-AI/Bilqis-MLX/commit/3b0c1775e0d5c2cb7eb76a8d3a97b64282746a1e) `refactor(bamf): keep semantic boundary guard hygiene-clean`
- [`cf82c7d1b26c`](https://github.com/Entif-AI/Bilqis-MLX/commit/cf82c7d1b26cad368778596a001b627042bcc796) `docs(bamf): refresh A12.2 turn-in custody`
- [`9119d7265d55`](https://github.com/Entif-AI/Bilqis-MLX/commit/9119d7265d555124c2396fcae0e48122ca807e91) `fix(bamf): reject package-imported Atlas aliases`
- [`eb4e7b81aca1`](https://github.com/Entif-AI/Bilqis-MLX/commit/eb4e7b81aca10223e59b94448b7cd29e4a25f2ba) `docs(bamf): refresh A12.2 review custody`
- [`309c727a7fa3`](https://github.com/Entif-AI/Bilqis-MLX/commit/309c727a7fa33401a18442bb652a2e55413a4e69) `Merge remote-tracking branch 'origin/codex/bamf02-a12-2-428-20261105' into codex/bamf-unified-base-20261028`
- [`3f65f15cb9b6`](https://github.com/Entif-AI/Bilqis-MLX/commit/3f65f15cb9b6b28e8640111b595ee231cbcb63e3) `docs(bamf): reconcile A12.2 post-merge custody`
- [`19b95443b74c`](https://github.com/Entif-AI/Bilqis-MLX/commit/19b95443b74c535416db632e6405dc3abe53a009) `docs(bamf): classify A12.2 custody PR`
- [`7e4f92e06229`](https://github.com/Entif-AI/Bilqis-MLX/commit/7e4f92e062299909dd47b547b8b4897a189c3738) `Merge pull request #870 from Entif-AI/codex/bamf02-a12-2-428-postmerge-custody-20261105`
- [`134e9a61d44b`](https://github.com/Entif-AI/Bilqis-MLX/commit/134e9a61d44b837a61d7547c5d9cda311719b8fc) `test(bamf): prove source-qualified B13 continuation`
- [`22ead2c7c268`](https://github.com/Entif-AI/Bilqis-MLX/commit/22ead2c7c268bacc918718e1edbc5aafe96fa54c) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/bamf02-b-708-c05-owner-20261105`
- [`20b43ad3ecdf`](https://github.com/Entif-AI/Bilqis-MLX/commit/20b43ad3ecdfe68f9c10f69244164bd554a4ba7e) `test(bamf): prove A12.3 source successor boundaries`
- [`21fc0422f6c7`](https://github.com/Entif-AI/Bilqis-MLX/commit/21fc0422f6c777a62fc0688424287f69418bbd22) `docs(bamf): turn in A12.3 candidate`
- [`30982dfa6e80`](https://github.com/Entif-AI/Bilqis-MLX/commit/30982dfa6e805c41da680f3c54e3c13056b54989) `test(bamf): require semantic continuation parity`
- [`818743a56b2f`](https://github.com/Entif-AI/Bilqis-MLX/commit/818743a56b2fcbc202ae624c13e4184b072422dd) `chore(bamf): reconcile current issue mirrors`
- [`63f0fcc81257`](https://github.com/Entif-AI/Bilqis-MLX/commit/63f0fcc81257622d8487bd6b01183b2fb7de69d5) `docs(bamf): record A12.3 turn-in PR`
- [`cc6c0dfead8a`](https://github.com/Entif-AI/Bilqis-MLX/commit/cc6c0dfead8a03553ce8d146af6956df7085104c) `Merge pull request #871 from Entif-AI/codex/bamf02-a12-3-429-20261105`
- [`de07dcefe064`](https://github.com/Entif-AI/Bilqis-MLX/commit/de07dcefe06493995819aad8a6d75d236ded438d) `docs(bamf): reconcile A12.3 post-merge custody`
- [`06c421641693`](https://github.com/Entif-AI/Bilqis-MLX/commit/06c421641693b58320db1c3824a68788e521b67a) `docs(bamf): classify A12.3 custody PR`
- [`f831310917aa`](https://github.com/Entif-AI/Bilqis-MLX/commit/f831310917aa04d6daabaf4e919185587e344935) `fix(bamf): preserve foundation evidence authority`
- [`22d23ddfc5cc`](https://github.com/Entif-AI/Bilqis-MLX/commit/22d23ddfc5cc2781c5ae210d0c1185c6176753fb) `Merge pull request #873 from Entif-AI/codex/bamf02-a12-3-429-postmerge-custody-20261105`
- [`1b69365e9e2b`](https://github.com/Entif-AI/Bilqis-MLX/commit/1b69365e9e2bf2bf1087bb09433915916c8462ab) `test(bamf): prove A12.3 held boundaries directly`
- [`97300f464a7c`](https://github.com/Entif-AI/Bilqis-MLX/commit/97300f464a7c274f2e639b6946544e8ecd40f0cb) `docs(bamf): turn in A12.3 boundary proof`
- [`eb4219907dfc`](https://github.com/Entif-AI/Bilqis-MLX/commit/eb4219907dfc738c843cbba00765e4294426d351) `docs(bamf): record A12.3 remediation PR`
- [`86ee58c49f39`](https://github.com/Entif-AI/Bilqis-MLX/commit/86ee58c49f3969bbcd8d5ee4386ec219e86f7321) `fix(bamf): clear remediation quality gates`
- [`93233f86849f`](https://github.com/Entif-AI/Bilqis-MLX/commit/93233f86849f374ce5026291d4fd5cfa902a2e31) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/bamf02-b-708-c05-owner-20261105`
- [`4cffd8c79cbb`](https://github.com/Entif-AI/Bilqis-MLX/commit/4cffd8c79cbb5021cedce225118448af58a68253) `Merge pull request #874 from Entif-AI/codex/bamf02-a12-3-429-boundary-proof-20261105`
- [`4e839b62c035`](https://github.com/Entif-AI/Bilqis-MLX/commit/4e839b62c035fdf44b9cfc189699bd8b683c2db2) `docs(bamf): reconcile final A12.3 custody`
- [`6bd2e28d2483`](https://github.com/Entif-AI/Bilqis-MLX/commit/6bd2e28d24832b4e9f6a158cab3b123ba388f199) `docs(bamf): classify final A12.3 custody PR`
- [`ba7d3846891e`](https://github.com/Entif-AI/Bilqis-MLX/commit/ba7d3846891e16d3124e2ce223ace6b9e943c42f) `Merge pull request #875 from Entif-AI/codex/bamf02-a12-3-429-final-custody-20261105`
- [`1a31e56493df`](https://github.com/Entif-AI/Bilqis-MLX/commit/1a31e56493df5b7c4a4602fe44669636fbf22d7f) `ci: follow compartmentalized verification paths`
- [`89f53f4dcc29`](https://github.com/Entif-AI/Bilqis-MLX/commit/89f53f4dcc295d1dd957095e56ee3797c9ea5843) `refactor(bamf): compartmentalize remediation surfaces`
- [`aaf24bc95cf8`](https://github.com/Entif-AI/Bilqis-MLX/commit/aaf24bc95cf83d02e34b0763e7f58cabeaf7e071) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/bamf02-b-708-c05-owner-20261105`
- [`1dff80cdd616`](https://github.com/Entif-AI/Bilqis-MLX/commit/1dff80cdd61651613bdd1af2a82644cb99f4fef9) `chore(bamf): refresh remediation quality evidence`
- [`aeeba85e7ff0`](https://github.com/Entif-AI/Bilqis-MLX/commit/aeeba85e7ff06a671d92bbb3d161bc963d96b470) `ci: follow moved SKOS policy test path`
- [`b16941114dee`](https://github.com/Entif-AI/Bilqis-MLX/commit/b16941114dee33247ee9a9e6c013797b9d82af27) `fix(bamf): consolidate the EGM-Mitigation #708, #709, #710 and #711 remediations`
- [`e8021fe7ebee`](https://github.com/Entif-AI/Bilqis-MLX/commit/e8021fe7ebee4c2fea1c197d62cdaa313dd4bec6) `docs(bamf): close B09.2 acceptance receipt`
- [`2fa5e875aacf`](https://github.com/Entif-AI/Bilqis-MLX/commit/2fa5e875aacf18b2d26fd7354053ec2904818546) `docs(bamf): close B09.2 acceptance receipt`
- [`1212b5faa371`](https://github.com/Entif-AI/Bilqis-MLX/commit/1212b5faa371e54b4f6a896c225a2ecb72a68df5) `docs(bamf): bind B12.2 completion evidence`
- [`e99630d4812a`](https://github.com/Entif-AI/Bilqis-MLX/commit/e99630d4812a852589dae55dac61bd398b3fba08) `Merge reviewed unified into B12.2 closeout`
- [`b33a72672a25`](https://github.com/Entif-AI/Bilqis-MLX/commit/b33a72672a25fe5768fa4da41c7b5a9451951274) `docs(bamf): close B12.1 acceptance receipt`
- [`6573d66e56c4`](https://github.com/Entif-AI/Bilqis-MLX/commit/6573d66e56c40fc0009ee2ae9d7aff1cab37a959) `test(bamf): bind C02 real-source proof to batch authority`
- [`af4953cdb198`](https://github.com/Entif-AI/Bilqis-MLX/commit/af4953cdb1981168127699cfa80db819e8ab0f47) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/bamf02-c02-1-490-20261106`
- [`acb47e98b3bd`](https://github.com/Entif-AI/Bilqis-MLX/commit/acb47e98b3bdcdd82c8297135fc78b7f6bf5b50c) `docs(bamf): close B12.1 acceptance receipt`
- [`0afb12a08848`](https://github.com/Entif-AI/Bilqis-MLX/commit/0afb12a08848a6f2aba3b83b26f1466ea708d857) `docs(bamf): close B12.2 transaction acceptance`
- [`d622ca3649ef`](https://github.com/Entif-AI/Bilqis-MLX/commit/d622ca3649efbe23bc6fd760d17823d0e8292df6) `chore(bamf): activate B12.3 completion work`
- [`657e4c3a1070`](https://github.com/Entif-AI/Bilqis-MLX/commit/657e4c3a107077d56fdf3c268ec601146ba1681e) `docs(bamf): close C02.1 acceptance receipt`
- [`1c5f30179e70`](https://github.com/Entif-AI/Bilqis-MLX/commit/1c5f30179e70c4fd29e964b28fa413e80161b043) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/bamf02-c02-1-490-20261106`
- [`2d8993c7aa65`](https://github.com/Entif-AI/Bilqis-MLX/commit/2d8993c7aa654378b13ce9e14e7f0bf0986083b4) `docs(bamf): record final C02.1 unified intake`
- [`aef69dae9179`](https://github.com/Entif-AI/Bilqis-MLX/commit/aef69dae9179bb09f85f955b8a494f6582eac942) `test(bamf): complete C02.1 source-authority requalification`
- [`67dd6ab976e4`](https://github.com/Entif-AI/Bilqis-MLX/commit/67dd6ab976e4e6c2be7ffed270b9636955178d5a) `feat(bamf): complete B12.3 optimizer clock semantics`
- [`540519899454`](https://github.com/Entif-AI/Bilqis-MLX/commit/540519899454065d9d44331a9809511838d5aee3) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/bamf02-b12-3-476-complete-20261106`
- [`1826a53502cb`](https://github.com/Entif-AI/Bilqis-MLX/commit/1826a53502cbbb6cc11877f7f3bf0f01188152e4) `fix(bamf): harden B13.1 publication custody`
- [`ebbb43b744c4`](https://github.com/Entif-AI/Bilqis-MLX/commit/ebbb43b744c476bfbde64477c80bc115fb1761f9) `docs(bamf): activate B13.1 completion turn-in`
- [`04970b60575f`](https://github.com/Entif-AI/Bilqis-MLX/commit/04970b60575f5aa8c95f495ed3322355aeafd131) `docs(bamf): bind B13.1 turn-in PR`
- [`e50d759cc45b`](https://github.com/Entif-AI/Bilqis-MLX/commit/e50d759cc45bf61807f62ee62d7354052a3f0db8) `docs(bamf): refresh B13.1 final evidence`
- [`9f6bca1190c0`](https://github.com/Entif-AI/Bilqis-MLX/commit/9f6bca1190c04ab84cbf959a95be87ad5207b501) `docs(bamf): park B13.1 on A02 admission`
- [`0b2cb9e17c3e`](https://github.com/Entif-AI/Bilqis-MLX/commit/0b2cb9e17c3e78d999611980543396b60cb7638d) `refactor(bamf): harden B12.3 optimizer migration`
- [`760b3a75417c`](https://github.com/Entif-AI/Bilqis-MLX/commit/760b3a75417c95269636f75c3e832f20bfeb665d) `docs(bamf): record B12.3 EGM availability blocker`
- [`a5c25eb140f1`](https://github.com/Entif-AI/Bilqis-MLX/commit/a5c25eb140f1af05ad2b270ed38f7a2b5af42230) `docs(bamf): record B12.3 EGM pass and PR`
- [`3899649586b1`](https://github.com/Entif-AI/Bilqis-MLX/commit/3899649586b105b075e92f0ee3c51e80c379b473) `feat(bamf): complete B12.3 optimizer clock semantics`
- [`f77a37eaba38`](https://github.com/Entif-AI/Bilqis-MLX/commit/f77a37eaba3885795f068077053a094c7e7cb625) `feat(bamf): complete A02 production vocabulary admission`
- [`9dac486a06ea`](https://github.com/Entif-AI/Bilqis-MLX/commit/9dac486a06ea8a5ae70a1ec6b93afa20a2aa7bdb) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/bamf02-a-399-production-admission-20261106`
- [`6a0b8ccd0b5c`](https://github.com/Entif-AI/Bilqis-MLX/commit/6a0b8ccd0b5cb38c47c20a5b4e376fac35254b77) `docs(bamf): turn in A02.1 production admission`
- [`0a24c5eebc27`](https://github.com/Entif-AI/Bilqis-MLX/commit/0a24c5eebc278698084114e347e8876e9930ef64) `docs(bamf): link A02.1 turn-in PR`
- [`48b262e947b0`](https://github.com/Entif-AI/Bilqis-MLX/commit/48b262e947b0a2b5eaa855f9a7a07e435e3ea2bb) `fix(bamf): reuse digest validation contract`
- [`a2d784144aca`](https://github.com/Entif-AI/Bilqis-MLX/commit/a2d784144aca1fad9be8f0bb213d5ea9c769e304) `refactor(bamf): split parameter extension validation`
- [`fef4146c3bad`](https://github.com/Entif-AI/Bilqis-MLX/commit/fef4146c3bad484ae9cb5e608618b3eb6e4a9c5e) `feat(bamf): reconcile B12.4 optimizer manifest authority`
- [`f1991ae815ea`](https://github.com/Entif-AI/Bilqis-MLX/commit/f1991ae815ea3d466c41a1e6982d3c8218152535) `docs(bamf): record B12.4 production reconciliation`
- [`87a41212713a`](https://github.com/Entif-AI/Bilqis-MLX/commit/87a41212713a913e9760706abb301f3bfecb9563) `test(bamf): harden B12.4 manifest proof`
- [`253efc4c2a55`](https://github.com/Entif-AI/Bilqis-MLX/commit/253efc4c2a554f4af9a3f789e8491129b21115cc) `feat(bamf): complete C02 factory training composition`
- [`dbbe506d8b48`](https://github.com/Entif-AI/Bilqis-MLX/commit/dbbe506d8b4845f803499614aebd72a1ff865bee) `fix(bamf): align affected integration authority regressions`
- [`eb486d0125e9`](https://github.com/Entif-AI/Bilqis-MLX/commit/eb486d0125e92ad59d8532e4f0657f4c3d080773) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/bamf02-c02-371-complete-20261106`
- [`f90c54ab945b`](https://github.com/Entif-AI/Bilqis-MLX/commit/f90c54ab945bd49016523d287d410256d26e36cf) `fix(bamf): restore C07 vocabulary admission boundary`
- [`8457161520ae`](https://github.com/Entif-AI/Bilqis-MLX/commit/8457161520ae02173ef7c021e0cd7916b66467fc) `fix(bamf): enforce staged A02 handoff to C07`
- [`8de6030e84d3`](https://github.com/Entif-AI/Bilqis-MLX/commit/8de6030e84d382499d90f4d9b85c595b30e4e19a) `docs(bamf): park A02.1 on C07 adoption owner`
- [`7326a17f14c6`](https://github.com/Entif-AI/Bilqis-MLX/commit/7326a17f14c6e0e0cfb3da86cb9f6701a01eabff) `docs(bamf): preserve A02.1 in WAITING queue`
- [`ba1c366e8f58`](https://github.com/Entif-AI/Bilqis-MLX/commit/ba1c366e8f583d1c0bb2676a7740c749707e7fa1) `docs(bamf): record A02 staging witness pass`
- [`43226cbfa404`](https://github.com/Entif-AI/Bilqis-MLX/commit/43226cbfa4049706eecebdb37ffca16135e6f6d3) `chore(bamf): activate A09.5a realization child`
- [`96e443d44e8a`](https://github.com/Entif-AI/Bilqis-MLX/commit/96e443d44e8a089fc20429e9b888a2789e6556cb) `fix(bamf): compose C02 production training authority`
- [`daaabc2872d4`](https://github.com/Entif-AI/Bilqis-MLX/commit/daaabc2872d4da624f34c22c1a842c20cee7a508) `test(bamf): use valid numeric construction scope`
- [`b145acc9cd13`](https://github.com/Entif-AI/Bilqis-MLX/commit/b145acc9cd137140b4e3d2a7c6a04a68e805ef15) `fix(factory): accept exact primary-source candidates`
- [`3bee16f3bcd0`](https://github.com/Entif-AI/Bilqis-MLX/commit/3bee16f3bcd0900915b05221694b6c2a1ef187bf) `feat(factory): promote D event source realizations`
- [`ad9b6612715e`](https://github.com/Entif-AI/Bilqis-MLX/commit/ad9b6612715e12ae3073820c4c092476ac7cebf4) `fix(factory): stage event identities incrementally`
- [`658507d5bcde`](https://github.com/Entif-AI/Bilqis-MLX/commit/658507d5bcde10afee72bbadd8d781102762b6be) `docs(bamf): record C02 repair and turn-in evidence`
- [`7ac000dd643e`](https://github.com/Entif-AI/Bilqis-MLX/commit/7ac000dd643e12a88e8ffc8aa1ebb84e95b6be2e) `docs(bamf): clean C02 receipt formatting`
- [`dc67a3c8d2d6`](https://github.com/Entif-AI/Bilqis-MLX/commit/dc67a3c8d2d6edbf9ca63dcd6ed105d9fed4909c) `fix(bamf): bind C02 compilation to topology authority`
- [`6a3466122dfb`](https://github.com/Entif-AI/Bilqis-MLX/commit/6a3466122dfbd93b4e41e705558059be01c0a07a) `fix(bamf): bind candidate decay to B01 authority`
- [`c77471968e78`](https://github.com/Entif-AI/Bilqis-MLX/commit/c77471968e78a06d2695352c9fa9da299d42a5fc) `docs(bamf): record B12.4 mitigation head`
- [`d0dc79d825f4`](https://github.com/Entif-AI/Bilqis-MLX/commit/d0dc79d825f43d8ba4d732a2b668817692db67d9) `feat(factory): wire event successor realizations`
- [`c7d69da261d9`](https://github.com/Entif-AI/Bilqis-MLX/commit/c7d69da261d96bf46b2be2695e54820f91a4ee06) `docs(bamf): record A09.5 realization readiness`
- [`a11487a94318`](https://github.com/Entif-AI/Bilqis-MLX/commit/a11487a94318b2eeee08972a6187acc9cddbec32) `docs(bamf): attach A09.5 realization PR`
- [`fdb53084dc9b`](https://github.com/Entif-AI/Bilqis-MLX/commit/fdb53084dc9b41860acb8b6e94fe757f18327342) `docs(bamf): park B12.4 after EGM pass`
- [`95b1a776ae79`](https://github.com/Entif-AI/Bilqis-MLX/commit/95b1a776ae79d03934d123845081ba71d6edf842) `docs(bamf): correct B12.4 PR admission under ADR-128`
- [`28c81d07ae9d`](https://github.com/Entif-AI/Bilqis-MLX/commit/28c81d07ae9dd0bfbba9272274d19b5f4357fde6) `refactor(factory): split event realization authority`
- [`f4ccabcd22dd`](https://github.com/Entif-AI/Bilqis-MLX/commit/f4ccabcd22dd33ef604d98072c362a9dd9d315e5) `docs(bamf): record A09.5 hosted repair`
- [`b1479852c49e`](https://github.com/Entif-AI/Bilqis-MLX/commit/b1479852c49e1e8760e7d74a6c0eea84ef0486e2) `docs(bamf): record B12.4 turn-in PR`
- [`f9f87d8b613a`](https://github.com/Entif-AI/Bilqis-MLX/commit/f9f87d8b613a128d672cfbb6ca7c15dc4b839f90) `docs(bamf): finalize C02 exact-head evidence`
- [`c7bcb9678e85`](https://github.com/Entif-AI/Bilqis-MLX/commit/c7bcb9678e85e672c3645038a1f1077fbea88c32) `fix(factory): isolate event realization staging`
- [`a42c8e207da8`](https://github.com/Entif-AI/Bilqis-MLX/commit/a42c8e207da804813b408af1dc92245d168f0fb5) `docs(bamf): record A09.5 preflight repairs`
- [`db7fd553a2e5`](https://github.com/Entif-AI/Bilqis-MLX/commit/db7fd553a2e5deac65574851a16f34e8303a1b90) `fix(bamf): reconcile B12.4 optimizer manifest authority`
- [`65a3278cee99`](https://github.com/Entif-AI/Bilqis-MLX/commit/65a3278cee992f174b7c7789cc3329dea911ba92) `refactor(bamf): split Factory bridge preparation`
- [`3e959177314f`](https://github.com/Entif-AI/Bilqis-MLX/commit/3e959177314fbd43def41547fd34a1e1701c8909) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/bamf02-c02-371-complete-20261106`
- [`fcc634914e75`](https://github.com/Entif-AI/Bilqis-MLX/commit/fcc634914e75fc2df4389b45b8db9a69854e4a2d) `fix(bamf): bind Atlas feature reads to correction owner`
- [`d5be23a5cec4`](https://github.com/Entif-AI/Bilqis-MLX/commit/d5be23a5cec4bd80bb5d77b0498a474503d2fc77) `fix(c09): gate packed-frame reads on correction holds`
- [`dcf02980179b`](https://github.com/Entif-AI/Bilqis-MLX/commit/dcf02980179bf8829d3754d8b553972f17da3f21) `fix(c09): preserve canonical source dependency keys`
- [`35deb51fc9a7`](https://github.com/Entif-AI/Bilqis-MLX/commit/35deb51fc9a758eef8ad188d303b9b23f50a7b63) `refactor(c09): isolate packed-frame eligibility gate`
- [`bbea78520013`](https://github.com/Entif-AI/Bilqis-MLX/commit/bbea785200131c10c4dbb5c413ca86297e6ef6d6) `fix(c09): gate exact cache reads on correction state`
- [`a720bcb20036`](https://github.com/Entif-AI/Bilqis-MLX/commit/a720bcb20036469ea2d073ae684d999e18458e3e) `refactor(c09): converge on canonical revalidation modules`
- [`01bf1c269ce2`](https://github.com/Entif-AI/Bilqis-MLX/commit/01bf1c269ce24a54e27f5e87ef5446ac2c448ac7) `fix(bamf): pin legacy trainer adaptation authority`
- [`fee90ee7974a`](https://github.com/Entif-AI/Bilqis-MLX/commit/fee90ee7974a6cf203e960662f27ea1598923398) `fix: bind C09 motif and composition holds to production owners`
- [`0b7c03841036`](https://github.com/Entif-AI/Bilqis-MLX/commit/0b7c03841036663745adf372373e4a6b325f2a81) `fix: bind capability support to accepted source provenance`
- [`2e8aebad26ec`](https://github.com/Entif-AI/Bilqis-MLX/commit/2e8aebad26ec231fd11790e7f095a9c8511d937c) `refactor: name capability support provenance fields`
- [`35bcb8f639b5`](https://github.com/Entif-AI/Bilqis-MLX/commit/35bcb8f639b5295e56c6586b49eba42092c9257b) `fix: complete C09 production owner correction custody`
- [`af893701663e`](https://github.com/Entif-AI/Bilqis-MLX/commit/af893701663e5a696785cfdd3e94e0361d188b26) `fix: preserve atlas feature custody on batch revalidation`
- [`58f356331201`](https://github.com/Entif-AI/Bilqis-MLX/commit/58f3563312013d8c8e0f0ae629d088d43c4df8b7) `fix: retain C09 holds across cache and support reloads`
- [`4cb08c808605`](https://github.com/Entif-AI/Bilqis-MLX/commit/4cb08c8086057a274ad13857e57ba76d08eecf98) `fix: preserve corrected composition and support custody`
- [`ac71ce47bed5`](https://github.com/Entif-AI/Bilqis-MLX/commit/ac71ce47bed566e36a4450d8b346357060023a74) `fix: harden durable C09 correction custody`
- [`eba9cd70dfc0`](https://github.com/Entif-AI/Bilqis-MLX/commit/eba9cd70dfc024b3746df1b6ce2ed3981ecd71a7) `fix: root cache authority in accepted generation custody`
- [`46d40ebe022d`](https://github.com/Entif-AI/Bilqis-MLX/commit/46d40ebe022d76de2af444cfcdf5b569b7c7d6a9) `fix: connect C09 owners to accepted correction stream`
- [`9057477f4d29`](https://github.com/Entif-AI/Bilqis-MLX/commit/9057477f4d29f67dec65cad83f6ded202cd924b2) `fix: complete C09 correction revalidation custody`
- [`0bd42a5479af`](https://github.com/Entif-AI/Bilqis-MLX/commit/0bd42a5479afed7a79340cac067c268cec6ad3ff) `fix(bamf): satisfy legacy authority hygiene gate`
- [`91c1482c5a6b`](https://github.com/Entif-AI/Bilqis-MLX/commit/91c1482c5a6b2c1772f85b8e8d781fcb9731609c) `refactor: split accepted C09 custody surfaces`
- [`36a282d2033c`](https://github.com/Entif-AI/Bilqis-MLX/commit/36a282d2033ce6860d7febb72ef75d598c292a1d) `fix: close C09 round-five custody gaps`
- [`6dcb4a9e8339`](https://github.com/Entif-AI/Bilqis-MLX/commit/6dcb4a9e8339843957c40d78bace59ae0a79fe45) `fix(factory): preserve canonical realization allocation order`
- [`2892b10ee8e9`](https://github.com/Entif-AI/Bilqis-MLX/commit/2892b10ee8e9ea4a09861619f9b9e6cfe8a5d1b6) `docs(bamf): record A09.5 allocation repair`
- [`1372ad716caf`](https://github.com/Entif-AI/Bilqis-MLX/commit/1372ad716caf1b34295f60afac558b826e10583c) `fix: adapt C09 recut to current unified contracts`
- [`f956f79af91a`](https://github.com/Entif-AI/Bilqis-MLX/commit/f956f79af91a5ebc1b8709fb24527dad36a58b1b) `fix(factory): align event projection with staged allocation`
- [`3a238db2060a`](https://github.com/Entif-AI/Bilqis-MLX/commit/3a238db2060acb4e6a0a4c1ed2a5eeb0f97a3505) `docs(bamf): record A09.5 projection repair`
- [`2b7df66a7120`](https://github.com/Entif-AI/Bilqis-MLX/commit/2b7df66a7120c92067d8a944ac3855db4a4bde31) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/bamf02-a09-5a-888-realizations-20261107`
- [`92ec2494887e`](https://github.com/Entif-AI/Bilqis-MLX/commit/92ec2494887ee2f756c4c420959f59e40d363007) `fix(bamf): pin latest legacy trainer adaptation source`
- [`4e2da0f6e56b`](https://github.com/Entif-AI/Bilqis-MLX/commit/4e2da0f6e56b73c3f43637ddb61766f464953991) `docs(bamf): record current unified for A09.5`
- [`53eba37e5c9d`](https://github.com/Entif-AI/Bilqis-MLX/commit/53eba37e5c9dd6ad065b1980fa4850c484aaa624) `feat(bamf): complete C02 Factory training integration`
- [`60a3a602031d`](https://github.com/Entif-AI/Bilqis-MLX/commit/60a3a602031da04ab0081644c374c0fef08652e3) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/bamf02-a09-5a-888-realizations-20261107`
- [`2e96162a7242`](https://github.com/Entif-AI/Bilqis-MLX/commit/2e96162a72425586e2e93311ac9877d4eae57277) `docs(bamf): record latest unified for A09.5`
- [`be2995aac0a4`](https://github.com/Entif-AI/Bilqis-MLX/commit/be2995aac0a482099292164ec0db0212f85419df) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/bamf02-a09-5a-888-realizations-20261107`
- [`73dd7902dd3b`](https://github.com/Entif-AI/Bilqis-MLX/commit/73dd7902dd3ba1611f4fb3a4f92fbe860a63c6dd) `docs(bamf): record C02-reviewed unified for A09.5`
- [`0a5d0343085a`](https://github.com/Entif-AI/Bilqis-MLX/commit/0a5d0343085a4e18cd64bf00fe25e74eb76f5cac) `fix(bamf): align C02 with optimizer manifest authority`
- [`04658949aeb8`](https://github.com/Entif-AI/Bilqis-MLX/commit/04658949aeb8388c780aa7eeac8746562c65898b) `fix: thread C09 owner through current B11 forward`
- [`009c9f141280`](https://github.com/Entif-AI/Bilqis-MLX/commit/009c9f14128030ebc8f4ce8bb8751a48f56da37b) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/752-final-recut-20261107`
- [`f72c77171c6e`](https://github.com/Entif-AI/Bilqis-MLX/commit/f72c77171c6e1ba8b0a36a875ce8cd83fc86e2ca) `fix: accept explicit stale trainer evidence qualifiers`
- [`cc94a04a3959`](https://github.com/Entif-AI/Bilqis-MLX/commit/cc94a04a3959d6ab0546bb6b55e9d387b3b853c1) `docs(bamf): record C02 post-merge repair proof`
- [`54e0b07eb1be`](https://github.com/Entif-AI/Bilqis-MLX/commit/54e0b07eb1beafbfea712a476140d45e2b937344) `fix(bamf): close B12 optimizer integration acceptance`
- [`58eb36bba195`](https://github.com/Entif-AI/Bilqis-MLX/commit/58eb36bba1958e0b3ca5d6aa3080260ccac3e9a1) `fix(bamf): restore C02 optimizer manifest authority`
- [`a18394d7a7bb`](https://github.com/Entif-AI/Bilqis-MLX/commit/a18394d7a7bb5fa301dec2b1f2cc62ff65f1c99d) `Merge current BAMF unified base into #752 final recut`
- [`93a36f077bad`](https://github.com/Entif-AI/Bilqis-MLX/commit/93a36f077bad85ed9ebb069cfb985cffbb4507c0) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/bamf02-b12-370-parent-closeout-20261107`
- [`43268a1fd70f`](https://github.com/Entif-AI/Bilqis-MLX/commit/43268a1fd70f7cc7ce6161b9deb2b63b84be7611) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/bamf02-a09-5a-888-realizations-20261107`
- [`06d22ae7acdc`](https://github.com/Entif-AI/Bilqis-MLX/commit/06d22ae7acdce72848c26a195ea81c70ee7c9258) `docs(bamf): disambiguate historical Prometheus evidence`
- [`b6f6a558adda`](https://github.com/Entif-AI/Bilqis-MLX/commit/b6f6a558addaaf16e5ccd94c2267fe338be19e54) `docs(c09): freeze #752 final remediation evidence`
- [`4868fea0392a`](https://github.com/Entif-AI/Bilqis-MLX/commit/4868fea0392adb9ad6e0971d9cf6d6a06be9c20f) `test(bamf): prove B12 production participation seam`
- [`9441a1f0757a`](https://github.com/Entif-AI/Bilqis-MLX/commit/9441a1f0757a725c70620c4f070d39f4771c615e) `test(bamf): isolate B12 production witness`
- [`92541368721a`](https://github.com/Entif-AI/Bilqis-MLX/commit/92541368721a988f3141d197e6eb5c7994274bb6) `docs(bamf): requalify C04 parent acceptance`
- [`3634f7ce21ba`](https://github.com/Entif-AI/Bilqis-MLX/commit/3634f7ce21ba3728727aeee91efd4ec4ce392701) `docs(bamf): add C04 completion receipt`
- [`e30dada146b8`](https://github.com/Entif-AI/Bilqis-MLX/commit/e30dada146b83000c7b30de62cdebaa87b2200e6) `docs(bamf): align C04 closeout with ADR-121 child state`
- [`ebd0cde499fa`](https://github.com/Entif-AI/Bilqis-MLX/commit/ebd0cde499fa1083fbb5b289f493be57de7fb649) `docs(bamf): bind C04 turn-in to open parent only`
- [`3409a2e8550a`](https://github.com/Entif-AI/Bilqis-MLX/commit/3409a2e8550aef08312c9ab2953adfe16e3cd540) `test(bamf): exercise C04 live B11 proposer seam`
- [`dbe99b17c7fd`](https://github.com/Entif-AI/Bilqis-MLX/commit/dbe99b17c7fd0e0834f5452aaa6569f749606cf2) `test(bamf): bind source authority through live C04 B11 proposer`
- [`9281f05c93b2`](https://github.com/Entif-AI/Bilqis-MLX/commit/9281f05c93b2e2ca1e6f58e51250e48fa48d7bae) `docs(bamf): bind C04 closeout to exact route witnesses`
- [`732a25d0a307`](https://github.com/Entif-AI/Bilqis-MLX/commit/732a25d0a307b2f1a503159f0da1af878ca688af) `docs(bamf): align C04 receipt with repaired B11 witness`
- [`5f02a471504e`](https://github.com/Entif-AI/Bilqis-MLX/commit/5f02a471504e08c3dc088584e6cac454917e72cd) `test(bamf): keep C04 bridge regression imports minimal`
- [`200effb8d4cb`](https://github.com/Entif-AI/Bilqis-MLX/commit/200effb8d4cb651f63ec9c9e828156aca71195ce) `fix(bamf): preserve git semantics in detached snapshots`
- [`87f9b79556ab`](https://github.com/Entif-AI/Bilqis-MLX/commit/87f9b79556ab81347f9814543ee264a4e925afa7) `test(bamf): prove real B11 motif participation reaches B12`
- [`e022ae0b9543`](https://github.com/Entif-AI/Bilqis-MLX/commit/e022ae0b95433b0476ad6f5409c199c3aa68f947) `docs(bamf): mark C04 parent requalified`
- [`09dcd4a290f8`](https://github.com/Entif-AI/Bilqis-MLX/commit/09dcd4a290f8c1f75f4e005d9026481e610e284e) `docs(bamf): record exact-head C04 review and replay boundary`
- [`75dfc6e5b8c9`](https://github.com/Entif-AI/Bilqis-MLX/commit/75dfc6e5b8c95ea48f880bcc096637d65bc9fb1e) `docs(bamf): record C04 final independent review`
- [`b0b6ce82755b`](https://github.com/Entif-AI/Bilqis-MLX/commit/b0b6ce82755bd168965bc45f57730900811cc828) `docs(bamf): disambiguate historical Prometheus evidence`
- [`791a83f06756`](https://github.com/Entif-AI/Bilqis-MLX/commit/791a83f067568cf218e9e7161e236368590de710) `fix(bamf): preserve Git semantics in ADR-132 detached snapshots`
- [`f5c76ee714b2`](https://github.com/Entif-AI/Bilqis-MLX/commit/f5c76ee714b2d233cc54eda25792b4cd59eb6996) `test(bamf): complete C04 parent requalification`
- [`bb8e83f03e38`](https://github.com/Entif-AI/Bilqis-MLX/commit/bb8e83f03e38b64018cfe357addd90a0a6d67297) `docs(bamf): disambiguate historical Prometheus evidence`
- [`8447418c3fa7`](https://github.com/Entif-AI/Bilqis-MLX/commit/8447418c3fa7afbefff50b7d59142f9dcf4f462e) `docs(bamf): bind B12 parent proof to real B11 execution`
- [`377151bfe605`](https://github.com/Entif-AI/Bilqis-MLX/commit/377151bfe605f350025a55123c77b7721fce2323) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/bamf02-b12-370-parent-closeout-20261107`
- [`1ea767836061`](https://github.com/Entif-AI/Bilqis-MLX/commit/1ea767836061d503deed5291031649f4e890063e) `test(bamf): prove production denominator participation`
- [`088a742d10a7`](https://github.com/Entif-AI/Bilqis-MLX/commit/088a742d10a71673385a4bbf320d26d42b874502) `fix(bamf): align source family and evidence authority`
- [`bdc85bd9995a`](https://github.com/Entif-AI/Bilqis-MLX/commit/bdc85bd9995ada3c89cec8127e0cc8a51a8daa96) `test(bamf): migrate executable and retention fixtures`
- [`3b5cf00fc6ce`](https://github.com/Entif-AI/Bilqis-MLX/commit/3b5cf00fc6ce731417f9347431bce07d99288b20) `refactor(teacher): split strategy population owners`
- [`73d72772fff3`](https://github.com/Entif-AI/Bilqis-MLX/commit/73d72772fff3395e22888553b7042af8af201a6c) `fix(baseline): restore scheduler numeric and solver boundaries`
- [`7c4c94c5bc9a`](https://github.com/Entif-AI/Bilqis-MLX/commit/7c4c94c5bc9a9a1129756306552c3c863d2422cf) `fix(bamf): close post-EGM C09 custody defects`
- [`b3ccee970820`](https://github.com/Entif-AI/Bilqis-MLX/commit/b3ccee9708204251f19d11719ae8eaa829a79f86) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/752-post-egm-h1-fixes-20261107`
- [`dc007e384368`](https://github.com/Entif-AI/Bilqis-MLX/commit/dc007e384368e883e460082a850210d1ae53ae42) `fix(teacher): keep population-control import at package owner`
- [`9be2ebf4f195`](https://github.com/Entif-AI/Bilqis-MLX/commit/9be2ebf4f195b5104c98a43f41ca33d21d86af2f) `refactor(learning): split lesson guidance owners`
- [`55490f41bdb1`](https://github.com/Entif-AI/Bilqis-MLX/commit/55490f41bdb17a2a9744a4270153328b12d66d19) `test(bamf): bind denominator proof to source authority`
- [`320778d47a88`](https://github.com/Entif-AI/Bilqis-MLX/commit/320778d47a8880ed33d76fc564853bbad6ef1ebf) `refactor(bamf): compartmentalize accepted C09 custody`
- [`c49e6e66d21b`](https://github.com/Entif-AI/Bilqis-MLX/commit/c49e6e66d21bf547ff9a451ad1f44653d9367ae8) `test(baseline): refresh authority and progression fixtures`
- [`81322cfe9f0b`](https://github.com/Entif-AI/Bilqis-MLX/commit/81322cfe9f0b34be39361d4045b661165f751e34) `feat(bamf): define C03 teacher lineage custody projection`
- [`31582efffc42`](https://github.com/Entif-AI/Bilqis-MLX/commit/31582efffc422628ac9b64a50859801fa066d346) `test(bamf): prove C03 grade-neutral parent acceptance`
- [`62bb18723fb9`](https://github.com/Entif-AI/Bilqis-MLX/commit/62bb18723fb9a7d089776dcced934366e1e41727) `test(baseline): migrate split fixtures and typed guidance`
- [`9c0ea575c6b2`](https://github.com/Entif-AI/Bilqis-MLX/commit/9c0ea575c6b22767e52aa69b6ba2a8f8a0955d0a) `docs(bamf): park C03 pending B13 adoption`
- [`76f456776c88`](https://github.com/Entif-AI/Bilqis-MLX/commit/76f456776c88a642f79f5a7fa0df01bc729edb04) `test(bamf): close B12 parent optimizer acceptance`
- [`890c7b1b32e0`](https://github.com/Entif-AI/Bilqis-MLX/commit/890c7b1b32e04b77431b6f26b2029c638cefbf6d) `fix(bamf): require host-issued correction custody`
- [`3e8174dfe1f6`](https://github.com/Entif-AI/Bilqis-MLX/commit/3e8174dfe1f6e1e3cc51328ac3e11cdf5d015577) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/752-post-egm-h1-fixes-20261107`
- [`8006216c9103`](https://github.com/Entif-AI/Bilqis-MLX/commit/8006216c9103e77f609ad75a6c7cf1c28759fd5a) `docs(bamf): record host-issued custody gate`
- [`47e8acdedc12`](https://github.com/Entif-AI/Bilqis-MLX/commit/47e8acdedc1245a807fcd5d21810d8bb8d554ff8) `fix(baseline): preserve historical compatibility boundaries`
- [`ede0822bdfa8`](https://github.com/Entif-AI/Bilqis-MLX/commit/ede0822bdfa8f9322db2e4dea7659183e378e52d) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/premerge-baseline-repair-20261107`
- [`5962925fd99a`](https://github.com/Entif-AI/Bilqis-MLX/commit/5962925fd99a4d62d316f4cc55a0b757bd3ebe72) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/bamf02-a09-5a-888-realizations-20261107`
- [`a47ac1a84790`](https://github.com/Entif-AI/Bilqis-MLX/commit/a47ac1a84790d0371a51747fedb7a0ea0466b260) `chore(bamf): reactivate A09.5 completion`
- [`da9998a386c8`](https://github.com/Entif-AI/Bilqis-MLX/commit/da9998a386c8d196a946667bf9e0c30fd9a3743d) `merge(bamf): combine A09.5 adapter with realization authority`
- [`78e5e4507853`](https://github.com/Entif-AI/Bilqis-MLX/commit/78e5e45078539da3005077b34f1316b95c1b8b5a) `fix(bamf): complete A09.5 event adapter integration`
- [`7fa9ace84dfa`](https://github.com/Entif-AI/Bilqis-MLX/commit/7fa9ace84dfac570fc814b1119b633692b49f69f) `chore(bamf): mark A09.5 ready for EGM`
- [`8e4fd3bee22c`](https://github.com/Entif-AI/Bilqis-MLX/commit/8e4fd3bee22cb2a9730a1d3f10ed219fe3dd4fad) `fix(bamf): preserve unique PR flow ownership`
- [`57a209c8ef08`](https://github.com/Entif-AI/Bilqis-MLX/commit/57a209c8ef08c7f2ca1d429949384edd13fde629) `chore(bamf): reopen A09.5 realization authority`
- [`9db840c6764e`](https://github.com/Entif-AI/Bilqis-MLX/commit/9db840c6764e8d51b503fce3dac61600a6503936) `fix(bamf): keep A09.5 active during EGM repair`
- [`6db84b898a45`](https://github.com/Entif-AI/Bilqis-MLX/commit/6db84b898a45add5900d4badfb3ab94c50fe6f78) `fix(bamf): decouple event source identity from provider code`
- [`e1034bb4626b`](https://github.com/Entif-AI/Bilqis-MLX/commit/e1034bb4626b4df1e8748b696f64ab80066aa663) `fix(test): preserve premerge policy context in detached runs`
- [`0606307da0bd`](https://github.com/Entif-AI/Bilqis-MLX/commit/0606307da0bd5eff6c0b35617dc929fdfa7e269d) `fix(test): invoke premerge runner with package context`
- [`015896c84ed0`](https://github.com/Entif-AI/Bilqis-MLX/commit/015896c84ed0504b70e88379cbd4a61070d4da09) `refactor(test): satisfy hosted structure gate`
- [`7a9a69886594`](https://github.com/Entif-AI/Bilqis-MLX/commit/7a9a698865942af92c04217064c2e648fb8039cf) `fix(bamf): preserve C09 correction lineage`
- [`a37912319610`](https://github.com/Entif-AI/Bilqis-MLX/commit/a37912319610d1cefca2d7d1f739c4ded430f423) `docs(bamf): record H2 repair closure`
- [`dbc6432ccf46`](https://github.com/Entif-AI/Bilqis-MLX/commit/dbc6432ccf46afe707ba44707e214528f7e1478f) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/754-cache-transition-20261105`
- [`e1f87a11e74f`](https://github.com/Entif-AI/Bilqis-MLX/commit/e1f87a11e74f8beae70273c2483ddb44e4cbd183) `fix(baseline): repair reviewed unified premerge regressions`
- [`947a4ddda2c1`](https://github.com/Entif-AI/Bilqis-MLX/commit/947a4ddda2c133cabec846b09d3b58d18732dcf1) `fix(test): preserve package context in detached premerge`
- [`afbaa7e70f0b`](https://github.com/Entif-AI/Bilqis-MLX/commit/afbaa7e70f0be705e8eac84241aec69d5b1fb5c8) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/754-cache-transition-20261105`
- [`e90a646607f5`](https://github.com/Entif-AI/Bilqis-MLX/commit/e90a646607f50f8acb8bf83075f2cbc61166d4af) `test(bamf): prove cold continuation ignores disposable caches`
- [`ac93e1c8806b`](https://github.com/Entif-AI/Bilqis-MLX/commit/ac93e1c8806b12651e6e3e998b658ecd37115e68) `fix(bamf): reconcile A09.5 realized frontier state`
- [`dfa8cc2b76e4`](https://github.com/Entif-AI/Bilqis-MLX/commit/dfa8cc2b76e4d021805fe7ad32a9daf43bfae292) `test(bamf): route cache transition through acceptance owner`
- [`223d2c367e43`](https://github.com/Entif-AI/Bilqis-MLX/commit/223d2c367e431dde93ce54dd9b1042690d187759) `merge: refresh BAMF unified before EGM H3`
- [`8f24c55a7e48`](https://github.com/Entif-AI/Bilqis-MLX/commit/8f24c55a7e489914020243226f13ef5318b21585) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/bamf02-a09-5a-888-realizations-20261107`
- [`814125a0e80f`](https://github.com/Entif-AI/Bilqis-MLX/commit/814125a0e80f54e59a7cf8dbc0995735845f2b4f) `refactor(bamf): split custody contract tests`
- [`6cd5515a8658`](https://github.com/Entif-AI/Bilqis-MLX/commit/6cd5515a865828b27b03ad69e5e4bebd163b3d09) `test(bamf): compartmentalize factory test families`
- [`2db8c9ce5e7c`](https://github.com/Entif-AI/Bilqis-MLX/commit/2db8c9ce5e7c9919726a60fbf077374e8892b3f1) `test(bamf): clean event package diff hygiene`
- [`421d3ed9de22`](https://github.com/Entif-AI/Bilqis-MLX/commit/421d3ed9de229cb357fc53063eb54462fce18869) `refactor(test): split atlas integration witness`
- [`794df9e29fef`](https://github.com/Entif-AI/Bilqis-MLX/commit/794df9e29fef8160e53aaa35d47276d1cd276a86) `test(bamf): exercise real disposable cache boundaries`
- [`254703ad600d`](https://github.com/Entif-AI/Bilqis-MLX/commit/254703ad600d1231172a26ec4d5a39045b47fe09) `test(bamf): prove production cache transitions`
- [`7ea9b2a2545f`](https://github.com/Entif-AI/Bilqis-MLX/commit/7ea9b2a2545f46cbb6d2e80b6ccd35ede6ffbfd6) `docs(bamf): refresh B13.3 remediation receipt`
- [`abab27505e5c`](https://github.com/Entif-AI/Bilqis-MLX/commit/abab27505e5c0842fdc4922ef81206371392d6c6) `fix(bamf): close A09.5 realization review gaps`
- [`b31abda68b57`](https://github.com/Entif-AI/Bilqis-MLX/commit/b31abda68b57da23c4f62ce2103aa3e126fe0f5b) `perf(bamf): keep cache identity on-device`
- [`3bedf7c3ddf1`](https://github.com/Entif-AI/Bilqis-MLX/commit/3bedf7c3ddf1e536261aeb5b0830441cd399dca5) `chore(bamf): checkpoint A09.5 repair`
- [`71c82d6c14e0`](https://github.com/Entif-AI/Bilqis-MLX/commit/71c82d6c14e02e201513abee7fe190211529a114) `docs(bamf): refresh B13.3 performance receipt`
- [`73785a21a737`](https://github.com/Entif-AI/Bilqis-MLX/commit/73785a21a737d9591ee905b4c993a65487474cf9) `fix(bamf): separate cache runtime and receipt identity`
- [`cc960275aed1`](https://github.com/Entif-AI/Bilqis-MLX/commit/cc960275aed17f9ef2b411dc886a4035b5736e07) `docs(bamf): pin B13.3 deterministic cache receipt`
- [`780414b36e6b`](https://github.com/Entif-AI/Bilqis-MLX/commit/780414b36e6bff1505743c683c4c1e332096a149) `test(bamf): keep cache receipts object-independent`
- [`978953bfa8ee`](https://github.com/Entif-AI/Bilqis-MLX/commit/978953bfa8ee664e45a253b71c8f7e56dfc3c103) `perf(bamf): weak-bind disposable cache parameters`
- [`beae73a57df1`](https://github.com/Entif-AI/Bilqis-MLX/commit/beae73a57df182fd478856a340b0685d861095b1) `docs(bamf): pin weak cache identity receipt`
- [`bd3657e170c8`](https://github.com/Entif-AI/Bilqis-MLX/commit/bd3657e170c8bdc046a7bb28524c0fb829ca7ce9) `fix(bamf): prove B13.3 cache transition custody`
- [`282ce3a86340`](https://github.com/Entif-AI/Bilqis-MLX/commit/282ce3a863404f9b81f698b57a15644828c58e8b) `fix: repair C09 H3 lifecycle defects for #752`
- [`5389b49e10d7`](https://github.com/Entif-AI/Bilqis-MLX/commit/5389b49e10d79fb0af6e8d3036daf7a0eddeb283) `merge: refresh BAMF unified after H3 repairs`
- [`97780aa3335b`](https://github.com/Entif-AI/Bilqis-MLX/commit/97780aa3335b7197f31d040e91a4b202161e9d9e) `fix: preserve unified generation acceptance contract move`
- [`54542e4e7738`](https://github.com/Entif-AI/Bilqis-MLX/commit/54542e4e77389cd38d1d7b9ba48f17e6614a347a) `docs: record #752 H3 remediation evidence`
- [`07a6115e11ee`](https://github.com/Entif-AI/Bilqis-MLX/commit/07a6115e11ee0b7784f35982b6a98da748c96164) `chore(bamf): reactivate #746 authority closure`
- [`22a0e9ad5ed4`](https://github.com/Entif-AI/Bilqis-MLX/commit/22a0e9ad5ed4f2b019c0262f0e7aced66eb6a0d9) `merge: sync #746 with reviewed BAMF unified bd3657e1`
- [`18f5f58ab240`](https://github.com/Entif-AI/Bilqis-MLX/commit/18f5f58ab240f3c7a23c19debc95fab03f3a8f42) `test: prove cold accepted progression authority for #752`
- [`7129e4a2707a`](https://github.com/Entif-AI/Bilqis-MLX/commit/7129e4a2707a7915ba1348e447cb07697b56c860) `fix: close C09 temporal and recovery audit gaps for #752`
- [`c39655c26f28`](https://github.com/Entif-AI/Bilqis-MLX/commit/c39655c26f2889c6b5b7912bef6483f6fcbcb5d2) `fix: preserve C09 temporal authority boundary for #752`
- [`643dd73cd0d9`](https://github.com/Entif-AI/Bilqis-MLX/commit/643dd73cd0d941728de1b5df53e3bca8ebfedd8a) `test: split accepted C09 recovery witnesses for #752`
- [`67c7eaed9371`](https://github.com/Entif-AI/Bilqis-MLX/commit/67c7eaed9371ab4112dd96750c6c76cef218d4da) `docs: reconcile #752 H3 residual audit`
- [`5f2aa2c1fea3`](https://github.com/Entif-AI/Bilqis-MLX/commit/5f2aa2c1fea34a25377654a903defe15866c09ce) `docs: bind #752 residual proof to split recovery tests`
- [`ebd5a417bb73`](https://github.com/Entif-AI/Bilqis-MLX/commit/ebd5a417bb73525a0853a03291dd1ee065d88357) `fix(bamf): close C12 package import authority chain`
- [`8240110b6917`](https://github.com/Entif-AI/Bilqis-MLX/commit/8240110b6917726b5f8b802481c931ec94917a5c) `chore(bamf): turn in 746 authority closure`
- [`92947eae4026`](https://github.com/Entif-AI/Bilqis-MLX/commit/92947eae4026abda20bfef234b05452f995b3d6d) `chore(bamf): record A09.5 review readiness`
- [`d7ca3d96644e`](https://github.com/Entif-AI/Bilqis-MLX/commit/d7ca3d96644e5a5e340cfc027864d0ac76c19414) `chore(bamf): activate 510 atomic adoption`
- [`172e8566c69e`](https://github.com/Entif-AI/Bilqis-MLX/commit/172e8566c69e374ad60236d8d7f3d21986773c20) `feat(bamf): add C07 prepared-successor executor`
- [`8a29f046e972`](https://github.com/Entif-AI/Bilqis-MLX/commit/8a29f046e972006e3cdd9cbefb3b823645e010ee) `fix(bamf): distinguish executor runtime failure`
- [`01978b7a7691`](https://github.com/Entif-AI/Bilqis-MLX/commit/01978b7a769134dd90436b1a939722dfbd250dbd) `chore(bamf): park 510 on accepted-run authority`
- [`c8c9675829e5`](https://github.com/Entif-AI/Bilqis-MLX/commit/c8c9675829e5d83a138fc33d8ca3d3dec05a1f12) `fix(c09): consume A13 context invalidations durably`
- [`e7ca7fb8ee49`](https://github.com/Entif-AI/Bilqis-MLX/commit/e7ca7fb8ee49f69f4b6364d55b646dc91b19d73b) `docs(c09): record #752 residual authority repair`
- [`b4cd68cf6a26`](https://github.com/Entif-AI/Bilqis-MLX/commit/b4cd68cf6a266a161ed633d376952652b0250764) `docs(c09): record qualified 752 residual proof`
- [`13698be8e4ce`](https://github.com/Entif-AI/Bilqis-MLX/commit/13698be8e4cec8ac9e6933715da20f47933b90a6) `fix(bamf): keep C07 executor package-private`
- [`d8bc2171f788`](https://github.com/Entif-AI/Bilqis-MLX/commit/d8bc2171f78851b403db1090e8e22d116cb373cb) `docs(bamf): pin hardened 510 executor head`
- [`a1360109a77e`](https://github.com/Entif-AI/Bilqis-MLX/commit/a1360109a77e89e1a80c0b3fb1369da85ce8cfcb) `chore(bamf): activate C05 evaluation custody`
- [`7db57cdca524`](https://github.com/Entif-AI/Bilqis-MLX/commit/7db57cdca52457403fd26a936f09b6944ce53ccc) `fix(bamf): preserve C05 evaluation source custody`
- [`fb5b8cad05b5`](https://github.com/Entif-AI/Bilqis-MLX/commit/fb5b8cad05b51a33bce467814a81cf80bc8f988b) `docs(bamf): park C05 evaluation custody`
- [`aa2da1d4e3bd`](https://github.com/Entif-AI/Bilqis-MLX/commit/aa2da1d4e3bd186ae32ab9f6190ad9ad201b0589) `chore(bamf): activate B10 request disposition`
- [`d63bd8f9f469`](https://github.com/Entif-AI/Bilqis-MLX/commit/d63bd8f9f4699087d67a6f4c740a9120a58ddf2a) `fix(bamf): derive B10 refinement request disposition`
- [`f323216534d7`](https://github.com/Entif-AI/Bilqis-MLX/commit/f323216534d70fb60dfc9c688340f9d89862dd00) `chore(bamf): activate A13 prefix authority`
- [`06ef583f0722`](https://github.com/Entif-AI/Bilqis-MLX/commit/06ef583f0722075bbb3bd1dbb8df6d931a1011b7) `fix(bamf): issue A13 compiled-prefix authority`
- [`9564c3aabdfc`](https://github.com/Entif-AI/Bilqis-MLX/commit/9564c3aabdfc0ad06623cfd9c07a93c40cb15d74) `docs(bamf): park B10 request disposition`
- [`f21e3fb722ea`](https://github.com/Entif-AI/Bilqis-MLX/commit/f21e3fb722ea760a60ec7582e0c1723107e1c2da) `docs(bamf): park A13 prefix authority`
- [`9901f118e177`](https://github.com/Entif-AI/Bilqis-MLX/commit/9901f118e177f933c40bff995c833c7f2bc754f4) `chore(bamf): register B13 generation-zero owner`
- [`77dd984fb57b`](https://github.com/Entif-AI/Bilqis-MLX/commit/77dd984fb57b75d16f2e368b6054dc72b333f512) `feat(bamf): add B13 generation-zero custody`
- [`21ba6732f2d2`](https://github.com/Entif-AI/Bilqis-MLX/commit/21ba6732f2d271c67e7dfa0fe43a71e3adcc4cae) `test(bamf): migrate genesis fixtures to B13 authority`
- [`88a3cd3b39cd`](https://github.com/Entif-AI/Bilqis-MLX/commit/88a3cd3b39cdc7a9e4908b0fcc0038a763c1a2b2) `test(bamf): bind custody fixtures to accepted genesis`
- [`ee5e4e708339`](https://github.com/Entif-AI/Bilqis-MLX/commit/ee5e4e7083393ddfc9e6906c60d3d19bad13f5e6) `test(bamf): align successor fixtures to genesis custody`
- [`e0377639f2e6`](https://github.com/Entif-AI/Bilqis-MLX/commit/e0377639f2e6a70f7c4c7305d63b31e6eefb9256) `test(bamf): preserve accepted parent motif custody`
- [`1bba69e385f2`](https://github.com/Entif-AI/Bilqis-MLX/commit/1bba69e385f2666a5a185aa9114a3f64cd3f7685) `test(bamf): harden generation-zero authority negatives`
- [`6f91ccf63528`](https://github.com/Entif-AI/Bilqis-MLX/commit/6f91ccf6352888411f76491b58d9e7e9234ec055) `docs(bamf): park B13 generation-zero custody`
- [`c3297ec4ba4d`](https://github.com/Entif-AI/Bilqis-MLX/commit/c3297ec4ba4d8c4a91a1bc2757d49c7d8ba27ec1) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/bamf02-c03-376-20261107`
- [`e6f022685f0b`](https://github.com/Entif-AI/Bilqis-MLX/commit/e6f022685f0b624b21761b37c30d5bc161e90af2) `chore(bamf): reactivate C03 visit identity`
- [`ee8c6ef91682`](https://github.com/Entif-AI/Bilqis-MLX/commit/ee8c6ef916826be2b991294371ee55e3211f3ba1) `feat(bamf): define C03 teacher visit identity`
- [`6efa4ebe619b`](https://github.com/Entif-AI/Bilqis-MLX/commit/6efa4ebe619b700de49b0942defada6a4919b225) `docs(bamf): park C03 visit identity`
- [`173642f2bdf5`](https://github.com/Entif-AI/Bilqis-MLX/commit/173642f2bdf5ae67ed949d48b2a22c7a7a934b8e) `chore(bamf): register C02 visit provenance transport`
- [`1bb49dcc693f`](https://github.com/Entif-AI/Bilqis-MLX/commit/1bb49dcc693f87b525ba1e28d6284499d8b78409) `feat(bamf): transport C03 visit provenance through C02`
- [`7575243148f3`](https://github.com/Entif-AI/Bilqis-MLX/commit/7575243148f383363348cb0f287704972ec4d869) `refactor(bamf): compartmentalize C02 training proofs`
- [`462aea288fa0`](https://github.com/Entif-AI/Bilqis-MLX/commit/462aea288fa097c96481e6c435ddd7dbfb0e7d53) `test(bamf): bind B12 authority witness to C03 visit provenance`
- [`88baf8718d5d`](https://github.com/Entif-AI/Bilqis-MLX/commit/88baf8718d5de1cc5c2830b16a564cac679de825) `fix(bamf): canonicalize visit provenance and relocated source root`
- [`59a6d6d814ed`](https://github.com/Entif-AI/Bilqis-MLX/commit/59a6d6d814ed16d2aec128bb186734e2afc72d81) `feat(bamf): stage three source-qualified event successors (A09.5)`
- [`5f8f3d4b42cc`](https://github.com/Entif-AI/Bilqis-MLX/commit/5f8f3d4b42cc4656020e4427c7d8e822825a36f9) `fix(bamf): close C12 package import authority chain`
- [`69756136b03d`](https://github.com/Entif-AI/Bilqis-MLX/commit/69756136b03df34d689feaa92523cc6ef4ce3fe5) `merge: refresh #752 against current BAMF unified`
- [`03e7a3c060bc`](https://github.com/Entif-AI/Bilqis-MLX/commit/03e7a3c060bc49962ccfe049417090ea2c1c6ec0) `docs(c09): checkpoint 752 against current unified`
- [`e727641a7721`](https://github.com/Entif-AI/Bilqis-MLX/commit/e727641a7721ca21a6ed88d00ffb7f2da37be924) `docs(bamf): prepare 718 integration review`
- [`291a283f80c7`](https://github.com/Entif-AI/Bilqis-MLX/commit/291a283f80c750b7ae81750ba692d9a47e5f0fca) `fix(bamf): bind c12 to opaque c09 authority`
- [`cc06bc5edf4a`](https://github.com/Entif-AI/Bilqis-MLX/commit/cc06bc5edf4af5f3739ecb9fbecefc5b325ce50e) `chore(bamf): reactivate B13.1 custody closure`
- [`81d2f176120b`](https://github.com/Entif-AI/Bilqis-MLX/commit/81d2f176120beb4a070bd006aa9bb089f05eb4f1) `docs(bamf): park 718 on c09 host authority`
- [`4fff3b7e8152`](https://github.com/Entif-AI/Bilqis-MLX/commit/4fff3b7e8152652b00d979acaf768cb2ad451827) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/bamf02-b13-1-478-complete-20261106`
- [`cf432a443617`](https://github.com/Entif-AI/Bilqis-MLX/commit/cf432a443617def11f56d553a979b54cff0b595c) `docs(bamf): correct B13.1 dependency direction`
- [`c3d5619e50d9`](https://github.com/Entif-AI/Bilqis-MLX/commit/c3d5619e50d98576caaeb324d8ec1de3403026f8) `fix(bamf): preserve visit provenance in row digests`
- [`eefcb1bc97ca`](https://github.com/Entif-AI/Bilqis-MLX/commit/eefcb1bc97ca88b27fe98727e367b13546db88a2) `docs(bamf): park C02 visit provenance`
- [`acbe3c05782b`](https://github.com/Entif-AI/Bilqis-MLX/commit/acbe3c05782b298918f96286657c950c9b867d20) `fix(bamf): persist custody directory ancestry before pointer`
- [`f6c53bc8bb3f`](https://github.com/Entif-AI/Bilqis-MLX/commit/f6c53bc8bb3fd5d370a1faab8d90a7ac83f87922) `docs(bamf): reconcile B13.1 EGM repair evidence`
- [`1b84e17b0d32`](https://github.com/Entif-AI/Bilqis-MLX/commit/1b84e17b0d32f92d3adc0f75dc955b7d8b23acc4) `docs(bamf): bind B13.1 repaired exact-head proof`
- [`a7ac31de92cb`](https://github.com/Entif-AI/Bilqis-MLX/commit/a7ac31de92cbba325f4263b5f6e8872d7434ff4a) `fix(bamf): durably persist fresh run root`
- [`d6c20a6270e7`](https://github.com/Entif-AI/Bilqis-MLX/commit/d6c20a6270e78e0f879ff2e4eeb06ec21e35f752) `docs(bamf): checkpoint #478 round-four repair`
- [`ee644401d122`](https://github.com/Entif-AI/Bilqis-MLX/commit/ee644401d12275c98e454156fd49193e57e5cead) `fix(bamf): bind A13 source context validity`
- [`dab1014776cf`](https://github.com/Entif-AI/Bilqis-MLX/commit/dab1014776cf5eab7251f26f514c9722407c3b3a) `docs(bamf): qualify #478 round-four repair`
- [`b3a3e9a91491`](https://github.com/Entif-AI/Bilqis-MLX/commit/b3a3e9a91491674932e67ad951d206b91954db24) `docs(bamf): record 906 temporal authority proof`
- [`4bedc397ec75`](https://github.com/Entif-AI/Bilqis-MLX/commit/4bedc397ec75c8d6316234ff1f8adf95bec9f3ed) `fix(bamf): authenticate accepted authority and run-root durability`
- [`f9d14b207218`](https://github.com/Entif-AI/Bilqis-MLX/commit/f9d14b207218c636f0b81d29059b4f6ae65ad6af) `Merge remote-tracking branch 'origin/codex/bamf02-b13-1-478-complete-20261106' into codex/bamf02-b13-1-478-complete-20261106`
- [`49f57e4ef799`](https://github.com/Entif-AI/Bilqis-MLX/commit/49f57e4ef799bea9f4565bde4be15c0815bf0d24) `docs(bamf): record complete round-four findings`
- [`0d864a8cac3c`](https://github.com/Entif-AI/Bilqis-MLX/commit/0d864a8cac3c903d72624e6c34200550d288dfee) `docs(bamf): bind combined #478 custody proof`
- [`d51bb12f2caa`](https://github.com/Entif-AI/Bilqis-MLX/commit/d51bb12f2caa0391f97d2409ef2791b9df800b6f) `fix(bamf): authenticate C12 package parent authority`
- [`ec9188d10112`](https://github.com/Entif-AI/Bilqis-MLX/commit/ec9188d10112bed5c0a42f138e9bceda81a4af1c) `docs(bamf): bind round-five C12 repair proof`
- [`94d5763dcedd`](https://github.com/Entif-AI/Bilqis-MLX/commit/94d5763dcedd049db65e0a080238786ca0f53542) `fix(bamf): preserve nul-framed handoff paths`
- [`f166cac5db1e`](https://github.com/Entif-AI/Bilqis-MLX/commit/f166cac5db1e217880ce706efb51408001c7231e) `docs(bamf): close #478 EGM episode ready`
- [`9301e41ef215`](https://github.com/Entif-AI/Bilqis-MLX/commit/9301e41ef215b9d035449c3260c7cd0f8ee0b5a7) `fix(bamf): complete B13.1 custody hardening`
- [`e7663a2619f5`](https://github.com/Entif-AI/Bilqis-MLX/commit/e7663a2619f5017a77ae6e2ee681f1ec80dab32a) `docs(bamf): record 829 round 6 acceptance`
- [`3b80a76c0aca`](https://github.com/Entif-AI/Bilqis-MLX/commit/3b80a76c0acafce79a061174554fb8ade0c62618) `fix(bamf): bind A13 temporal transition to policy authority`
- [`db27df4abb94`](https://github.com/Entif-AI/Bilqis-MLX/commit/db27df4abb9471b1593da36e86401b636ec5d09a) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/bamf02-a-906-temporal-context-20261107`
- [`e5e2a4b16e7c`](https://github.com/Entif-AI/Bilqis-MLX/commit/e5e2a4b16e7c94157360e12384bdce267553b5e3) `chore(bamf): reactivate B13.2 completion`
- [`62237b466651`](https://github.com/Entif-AI/Bilqis-MLX/commit/62237b4666513f7555d142d0b25fb0e001f87f81) `test(bamf): restore complete B13.2 custody witness`
- [`4e3b88262c79`](https://github.com/Entif-AI/Bilqis-MLX/commit/4e3b88262c79771138a3d7d97169394d73581c72) `docs(bamf): bind #906 authority repair evidence`
- [`48c2dbad8513`](https://github.com/Entif-AI/Bilqis-MLX/commit/48c2dbad85137b0589d64a9df8a1c2b062d48232) `docs(bamf): record #906 EGM pass`
- [`70308ec7b24b`](https://github.com/Entif-AI/Bilqis-MLX/commit/70308ec7b24b8bb197a6b5efc7a452defbe78b85) `docs(bamf): turn in #906`
- [`246e7ea3676f`](https://github.com/Entif-AI/Bilqis-MLX/commit/246e7ea3676f86330211f3f5d16d2aa352bc7c67) `merge(bamf): sync #829 with reviewed unified`
- [`f99321c01463`](https://github.com/Entif-AI/Bilqis-MLX/commit/f99321c01463a10b4f223432c057a89aa68400b7) `docs(bamf): bind #829 turn-in PR`
- [`095902f08a4c`](https://github.com/Entif-AI/Bilqis-MLX/commit/095902f08a4c6713cca8eda81a2f1eee3fb5566c) `feat(bamf): preserve local handoff evidence without upstream (#829 C01)`
- [`fd9ef2890149`](https://github.com/Entif-AI/Bilqis-MLX/commit/fd9ef2890149ab5ae395640ce980a20f13a388c6) `fix(bamf): produce source-owned A13 temporal context transitions`
- [`3b4a24c1870d`](https://github.com/Entif-AI/Bilqis-MLX/commit/3b4a24c1870daa93476ac5dbe30c0fc33afa4526) `docs(bamf): bind B13.2 completion proof`
- [`58dc31f85dd6`](https://github.com/Entif-AI/Bilqis-MLX/commit/58dc31f85dd6711887de8d774ab4518119dbd3d3) `docs(bamf): bind B13.2 to Microspenics authority`
- [`6885130ee74a`](https://github.com/Entif-AI/Bilqis-MLX/commit/6885130ee74afbd9b8361d98dd979358c6ecea9b) `docs(bamf): record B13.2 EGM pass`
- [`c83a9c274d1b`](https://github.com/Entif-AI/Bilqis-MLX/commit/c83a9c274d1b9d01d1e3b5d6af1a0e7732f1cc8d) `test(baseline): refresh learning owner census`
- [`e511de8e07e1`](https://github.com/Entif-AI/Bilqis-MLX/commit/e511de8e07e12e218d011ed532bb202587992ce5) `chore(c09): resume #752 after temporal authority merge`
- [`eda7ed87b928`](https://github.com/Entif-AI/Bilqis-MLX/commit/eda7ed87b928264da29582f6c4805620b16a79a3) `docs(bamf): bind B13.2 premerge pass`
- [`24ee3d80ee02`](https://github.com/Entif-AI/Bilqis-MLX/commit/24ee3d80ee0208fd62b6b8d1d84044cb42e24077) `docs(bamf): turn in B13.2 PR 909`
- [`b177af8cd545`](https://github.com/Entif-AI/Bilqis-MLX/commit/b177af8cd545d40454a9c7b26c9e4ab1f49fc640) `merge: integrate #906 authority into #752 remediation`
- [`cc48ac40d875`](https://github.com/Entif-AI/Bilqis-MLX/commit/cc48ac40d875f0c2ae8ffbdc70001dbfc4815334) `feat(bamf): complete generation custody and exact cold resume (#479 / BAMF-0.2 B13.2)`
- [`3c6d08cd119f`](https://github.com/Entif-AI/Bilqis-MLX/commit/3c6d08cd119fbf47b87147b65121b9aad2e1edc6) `test(c09): prove source-owned temporal invalidation end to end`
- [`cf1e46bb576b`](https://github.com/Entif-AI/Bilqis-MLX/commit/cf1e46bb576be119fe99e48ad113d7319d42ef43) `test(c09): close temporal invalidation authority seam`
- [`048242f4d895`](https://github.com/Entif-AI/Bilqis-MLX/commit/048242f4d895d70288711268aa9f72d3c9d5ab94) `docs(c09): freeze #752 H4 candidate`
- [`0290f00ff4a1`](https://github.com/Entif-AI/Bilqis-MLX/commit/0290f00ff4a1a6957bc82ff8786adf3646836204) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/752-post-egm-h1-fixes-20261107`
- [`5480830d1ca8`](https://github.com/Entif-AI/Bilqis-MLX/commit/5480830d1ca8a762b58e676a6ab33218e1bea54e) `docs(c09): freeze #752 H4 on current unified`
- [`29058d3bde6d`](https://github.com/Entif-AI/Bilqis-MLX/commit/29058d3bde6d3913a04e8849950eac8572fc4df4) `merge(bamf): reconcile generation-zero custody with accepted B13 authority`
- [`918694f83b9e`](https://github.com/Entif-AI/Bilqis-MLX/commit/918694f83b9e4773a0ba6affcdcaa6563b8da94b) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/904-b13-6-generation-zero-20261107`
- [`f8a47e4d434d`](https://github.com/Entif-AI/Bilqis-MLX/commit/f8a47e4d434d96f4d53ba08ddfb5ae844d7a8e5a) `test(bamf): split generation acceptance witnesses`
- [`584159e000a8`](https://github.com/Entif-AI/Bilqis-MLX/commit/584159e000a857bf7284d5ab5a3677a28702b316) `fix(bamf): authenticate accepted feature ancestry`
- [`35d632960c69`](https://github.com/Entif-AI/Bilqis-MLX/commit/35d632960c69eda71847aba6d5eeff026d74b149) `docs(bamf): refresh B13.6 merge-readiness evidence`
- [`72a3e5891098`](https://github.com/Entif-AI/Bilqis-MLX/commit/72a3e5891098adf0da2ea5b124483a394c0736f5) `docs(bamf): record B13.5 merge-readiness proof`
- [`b85a96a86910`](https://github.com/Entif-AI/Bilqis-MLX/commit/b85a96a86910ba7083fbef315ec31fe4c2cfc4a6) `fix(bamf): bind retained successor feature ancestry`
- [`4182cc6818d1`](https://github.com/Entif-AI/Bilqis-MLX/commit/4182cc6818d1cdc39b1e24f21890ae1a66032afe) `docs(bamf): record B13.5 round-one repair`
- [`adbe8e34e71f`](https://github.com/Entif-AI/Bilqis-MLX/commit/adbe8e34e71f66bf5b14854a340a9aab0dd23ecb) `fix(bamf): harden generation custody authority`
- [`4ff3294abfae`](https://github.com/Entif-AI/Bilqis-MLX/commit/4ff3294abfae8d39c25d6ba525dd1ba3bc6c7cf7) `fix(c09): preserve accepted authority boundaries`
- [`acc1500a4e36`](https://github.com/Entif-AI/Bilqis-MLX/commit/acc1500a4e36eed5de02dae6c280cef3d3e3ef6f) `docs(c09): record #752 H4 remediation`
- [`3218636f8c9f`](https://github.com/Entif-AI/Bilqis-MLX/commit/3218636f8c9f9d6ab9c3dfa110a31ca457eed941) `docs(bamf): qualify B13.5 round two`
- [`f7537a0a5874`](https://github.com/Entif-AI/Bilqis-MLX/commit/f7537a0a5874ef031d992f71ee86f42ee9447d71) `fix(c05): require accepted custody for package imports`
- [`fa667a8b0ad1`](https://github.com/Entif-AI/Bilqis-MLX/commit/fa667a8b0ad1cb6dba628b0771f69a4965e98a2c) `docs(c09): record #752 H4 round-two remediation`
- [`c609cd3a2644`](https://github.com/Entif-AI/Bilqis-MLX/commit/c609cd3a264444717f8aa59d65c5f0ce0a15c295) `fix(bamf): bind generation zero to Factory authority`
- [`0de31f080e81`](https://github.com/Entif-AI/Bilqis-MLX/commit/0de31f080e81ee49089351bbdebd4f5ce961e0e0) `docs(c09): record #752 H4 acceptance`
- [`f4a4766415e5`](https://github.com/Entif-AI/Bilqis-MLX/commit/f4a4766415e5cd784e7acd8d44e51011eb212414) `chore(bamf): turn in #752`
- [`b28451f4e58e`](https://github.com/Entif-AI/Bilqis-MLX/commit/b28451f4e58e1380a5984f94f6bef936c3e82cee) `chore(c09): satisfy portable error contracts`
- [`a211836f59a2`](https://github.com/Entif-AI/Bilqis-MLX/commit/a211836f59a2a7c4949d585f2e30060473a53a38) `fix(bamf): anchor historical generation acceptance`
- [`d4bad39a32a8`](https://github.com/Entif-AI/Bilqis-MLX/commit/d4bad39a32a80acbffdb9f891a906892ab2e9fab) `fix(bamf): close C09 accepted correction custody (#752)`
- [`be379153753e`](https://github.com/Entif-AI/Bilqis-MLX/commit/be379153753e58218b0ebe389da0824369e63bd7) `docs(bamf): record historical acceptance repair`
- [`b9438fa2d532`](https://github.com/Entif-AI/Bilqis-MLX/commit/b9438fa2d532bdf83663bc860f3d5230e4af9734) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/697-b13-5-reconcile-20261107`
- [`4d6f60901d12`](https://github.com/Entif-AI/Bilqis-MLX/commit/4d6f60901d12dcb9016776b3f4b43e9c4bda17da) `docs(bamf): reconcile B13.5 with current unified`
- [`7046f0c7d160`](https://github.com/Entif-AI/Bilqis-MLX/commit/7046f0c7d160e3e6f81323f967c92fa796c90731) `docs(bamf): classify round-two aggregate failures`
- [`d873cea0e448`](https://github.com/Entif-AI/Bilqis-MLX/commit/d873cea0e448f8adddf1b74102529bb8872ca584) `docs(bamf): finalize B13.5 round-two qualification`
- [`f61661b98791`](https://github.com/Entif-AI/Bilqis-MLX/commit/f61661b98791cd6962568219c6c6640a48967aa0) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/904-b13-6-generation-zero-20261107`
- [`9fb2b1308b22`](https://github.com/Entif-AI/Bilqis-MLX/commit/9fb2b1308b22caab399289bed7a6250b11ebf880) `fix(bamf): decouple feature retention from correction epochs`
- [`fa605fb3ab62`](https://github.com/Entif-AI/Bilqis-MLX/commit/fa605fb3ab6287a2df1c203106b3c078fee26cc6) `fix(bamf): enforce generation-zero owner authority`
- [`f8a3fb2a5c3b`](https://github.com/Entif-AI/Bilqis-MLX/commit/f8a3fb2a5c3bac7a97ec6991f06bfa1f2955c638) `test(bamf): route accepted-runtime fixtures through genesis`
- [`695fdad5851b`](https://github.com/Entif-AI/Bilqis-MLX/commit/695fdad5851b152a1d420b60ecbd4a465c2644c1) `fix(bamf): recognize genesis acceptance in support replay`
- [`1516473df7c0`](https://github.com/Entif-AI/Bilqis-MLX/commit/1516473df7c0e373f870e6a6214f8d724a6c92dd) `test(bamf): align accepted-runtime genesis fixtures`
- [`142f6e01b549`](https://github.com/Entif-AI/Bilqis-MLX/commit/142f6e01b54959c14ff40328c9e6b0b0c82b038f) `fix(bamf): fail closed on unbound successor publication`
- [`4bad7631eca8`](https://github.com/Entif-AI/Bilqis-MLX/commit/4bad7631eca877ee660bca72b0505cc34ad72fe7) `fix(bamf): split b01 authority error identities`
- [`4465799c7c97`](https://github.com/Entif-AI/Bilqis-MLX/commit/4465799c7c977c136cd7684df031f104db638748) `docs(bamf): record 904 major remediation proof`
- [`b701dac1c393`](https://github.com/Entif-AI/Bilqis-MLX/commit/b701dac1c3934691d869fc505e85c5965d6e1c75) `docs(bamf): record B13.5 round-two repairs`
- [`8d7819ad9e22`](https://github.com/Entif-AI/Bilqis-MLX/commit/8d7819ad9e2275a793863f6b3d3b89b868aac45d) `chore(bamf): queue 904 for fresh egm`
- [`b2d730d4f9b2`](https://github.com/Entif-AI/Bilqis-MLX/commit/b2d730d4f9b20bb238daec9ec58aed209daf789d) `fix(c09): complete direct dependency custody`
- [`c54c5da7722d`](https://github.com/Entif-AI/Bilqis-MLX/commit/c54c5da7722d2091ceff3e6de1aae87f22fd72d9) `docs(bamf): qualify B13.5 for round three`
- [`7b5798b69ac6`](https://github.com/Entif-AI/Bilqis-MLX/commit/7b5798b69ac6019219e0a697a6aeb9f30b5d0f6d) `fix(bamf): reject legacy parent acceptance capability`
- [`66cf30332173`](https://github.com/Entif-AI/Bilqis-MLX/commit/66cf30332173c69ad0909a4d3ad55a8186caa6fd) `test(bamf): split acceptance history contracts`
- [`6df4dcb27104`](https://github.com/Entif-AI/Bilqis-MLX/commit/6df4dcb2710492f1ac53ec86391dbf701b0baa69) `fix(bamf): close generation-zero authority mint bypass`
- [`de50c30d9112`](https://github.com/Entif-AI/Bilqis-MLX/commit/de50c30d9112169b856bc48660d806383c861104) `docs(bamf): record #904 round-4 repair proof`
- [`6e3bab9c68f7`](https://github.com/Entif-AI/Bilqis-MLX/commit/6e3bab9c68f7d63ff5c222e31318b0c4a2ccfbeb) `docs(bamf): qualify B13.5 for round four`
- [`48119c4d2909`](https://github.com/Entif-AI/Bilqis-MLX/commit/48119c4d2909e95191b19c1b4013652f43f2d3f6) `fix(c09): complete context revalidation custody`
- [`fd739a12d7b6`](https://github.com/Entif-AI/Bilqis-MLX/commit/fd739a12d7b65174225a7483b0b835e52314559c) `fix(bamf): preserve retained feature construction lineage`
- [`377c98c7a138`](https://github.com/Entif-AI/Bilqis-MLX/commit/377c98c7a138c6fe610209b05b2829fdd4a051db) `fix(bamf): reject unanchored v2 parent capability`
- [`abc6a15f4342`](https://github.com/Entif-AI/Bilqis-MLX/commit/abc6a15f4342792ab8df7967069d3bf8d458bd58) `fix(bamf): derive generation-zero foundation authority`
- [`49744709c4b0`](https://github.com/Entif-AI/Bilqis-MLX/commit/49744709c4b0897ae4edda19752c0d718603bf34) `test(bamf): bind custody fixtures to persisted extents`
- [`4e1121f1c62a`](https://github.com/Entif-AI/Bilqis-MLX/commit/4e1121f1c62a6b35c8bc903adc9b416b6a03610d) `test(bamf): bind step proof to custody extents`
- [`6dbd5e499409`](https://github.com/Entif-AI/Bilqis-MLX/commit/6dbd5e499409e922195663a2cd8f747334cb7827) `test(bamf): inherit successor sidecars from custody`
- [`c754a1be8c2b`](https://github.com/Entif-AI/Bilqis-MLX/commit/c754a1be8c2b11803a941361e964a85e9532f96a) `test(bamf): derive successor fixture authority from custody`
- [`7b91ba7a4700`](https://github.com/Entif-AI/Bilqis-MLX/commit/7b91ba7a4700cd20d27556ff9623e4801c99c563) `test(bamf): import custody successor helper directly`
- [`8bc2d1399fa7`](https://github.com/Entif-AI/Bilqis-MLX/commit/8bc2d1399fa7b05a4e395cd831e19b04bf74ba7b) `test(bamf): follow runtime owner package path`
- [`68d3f287122b`](https://github.com/Entif-AI/Bilqis-MLX/commit/68d3f287122b5ff8e70337e15655e225d073fa3a) `fix(bamf): iterate accepted feature lineage`
- [`a45965434143`](https://github.com/Entif-AI/Bilqis-MLX/commit/a459654341433e4a9397b17db6821096db876a03) `docs(bamf): qualify B13.5 for round five`
- [`a888d3fd3f88`](https://github.com/Entif-AI/Bilqis-MLX/commit/a888d3fd3f889401601ee81663fa5a29145043f9) `fix(c09): close residual correction custody gaps`
- [`750f076be91a`](https://github.com/Entif-AI/Bilqis-MLX/commit/750f076be91a2e54dc9ad68c70c5f49e849caaff) `chore(bamf): checkpoint 516 flow control`
- [`fede719f5938`](https://github.com/Entif-AI/Bilqis-MLX/commit/fede719f593823ca8cff4b629d7b4fc7bc4b4ae1) `docs(bamf): record capped B13.5 review failure`
- [`75c8bb16664a`](https://github.com/Entif-AI/Bilqis-MLX/commit/75c8bb16664a8a9a3943153d1a4e839cc609152c) `docs(bamf): correct capped B13.5 findings`
- [`fb4e3541ba01`](https://github.com/Entif-AI/Bilqis-MLX/commit/fb4e3541ba01b08ed69a040b63a9be7d04b7cb35) `fix(c09): preserve context correction custody`
- [`e85db7448e30`](https://github.com/Entif-AI/Bilqis-MLX/commit/e85db7448e305e46afb131934bebc178bed6c1c6) `chore(bamf): checkpoint 516 round-five repair`
- [`2d4d013eb8fb`](https://github.com/Entif-AI/Bilqis-MLX/commit/2d4d013eb8fb591bec6a79c85bb21575ddfecb81) `fix(bamf): bridge accepted feature lineage cutover`
- [`762051c3059d`](https://github.com/Entif-AI/Bilqis-MLX/commit/762051c3059dd833df0f48d897c62d689a07d623) `docs(bamf): record post-cap B13.5 repair`
- [`3def851e9c16`](https://github.com/Entif-AI/Bilqis-MLX/commit/3def851e9c169f4e70cd82e2d3f207eb811c2a40) `fix(bamf): disambiguate Atlas artifact roots`
- [`bf2f22db9eeb`](https://github.com/Entif-AI/Bilqis-MLX/commit/bf2f22db9eeb12906ac8af0630c39a2c49fc311d) `docs(bamf): make artifact authority pathless`
- [`a08c7ff2810a`](https://github.com/Entif-AI/Bilqis-MLX/commit/a08c7ff2810a91411797fc1de33a103a061c2eb7) `fix(c09): preserve concrete source provenance`
- [`4c3937a32c67`](https://github.com/Entif-AI/Bilqis-MLX/commit/4c3937a32c6752f1d91c177a5d4f777ee10c77de) `fix(bamf): resolve historical Atlas by content identity`
- [`8e7648f93765`](https://github.com/Entif-AI/Bilqis-MLX/commit/8e7648f93765da2be93b5b22958d6dd83278b882) `fix(atlas): preserve source selection error contract`
- [`d7ab354c2df8`](https://github.com/Entif-AI/Bilqis-MLX/commit/d7ab354c2df804ab2151e4bf1f1287e3bf5e2503) `chore(bamf): checkpoint 516 source provenance repair`
- [`14b53a81d952`](https://github.com/Entif-AI/Bilqis-MLX/commit/14b53a81d952e763a8c26dda6e49d65d5b6be63a) `fix(bamf): bind genesis features to source authority`
- [`aa203815dfbf`](https://github.com/Entif-AI/Bilqis-MLX/commit/aa203815dfbffb22d8bf82fd2a6a5fb70cab4e3d) `test(bamf): split v2 cutover witness setup`
- [`6b27397fa390`](https://github.com/Entif-AI/Bilqis-MLX/commit/6b27397fa3904f250906733e903df040d38c3e60) `docs(bamf): record pathless B13 mitigation qualification`
- [`42fc68f01a4c`](https://github.com/Entif-AI/Bilqis-MLX/commit/42fc68f01a4cf91f4a27a87035685939a027671f) `test(bamf): align successor fixtures with genesis custody`
- [`2a322dcce3b9`](https://github.com/Entif-AI/Bilqis-MLX/commit/2a322dcce3b9c40084043a0eb2e28729dd2bccaf) `fix(c09): retain late context custody`
- [`23a656c62047`](https://github.com/Entif-AI/Bilqis-MLX/commit/23a656c6204785d182e9cad3892e0c020007e1cc) `chore(bamf): checkpoint 516 late-context repair`
- [`9e77fff394e4`](https://github.com/Entif-AI/Bilqis-MLX/commit/9e77fff394e4e10cc0553bc45108adb1025752e9) `chore(bamf): checkpoint 904 round-five repair`
- [`5c8631690d7e`](https://github.com/Entif-AI/Bilqis-MLX/commit/5c8631690d7ed412dcb5d3a0fb717246cbd78014) `fix(c09): defer early context evidence`
- [`b40a05c06476`](https://github.com/Entif-AI/Bilqis-MLX/commit/b40a05c06476a356937b74eb69f913404f0438be) `chore(bamf): checkpoint 516 early-context repair`
- [`4be8e0845a7c`](https://github.com/Entif-AI/Bilqis-MLX/commit/4be8e0845a7ca9797b6b355ac1961ef1faa07fe3) `fix(bamf): bind generation zero to owner authority`
- [`ebfe14b4f061`](https://github.com/Entif-AI/Bilqis-MLX/commit/ebfe14b4f06193100f2ac6ad3791b91b46dc2e54) `chore(bamf): satisfy generation zero quality gates`
- [`9242b3f8d950`](https://github.com/Entif-AI/Bilqis-MLX/commit/9242b3f8d950efa6a080d90278122b0f092f54d3) `docs(bamf): classify post-cap aggregate`
- [`6645c777f03e`](https://github.com/Entif-AI/Bilqis-MLX/commit/6645c777f03e688a19fa42ddb7067427b0dc7b8e) `fix(c09): retain learned execution dependencies`
- [`75a81cb6c286`](https://github.com/Entif-AI/Bilqis-MLX/commit/75a81cb6c286401700e528ae0a36200e4146648b) `chore(bamf): checkpoint 516 learned-dependency repair`
- [`395c4bc7d605`](https://github.com/Entif-AI/Bilqis-MLX/commit/395c4bc7d6058a4afcf8dcef7acfff57533390b9) `test(bamf): replay genesis feature authority in cache fixtures`
- [`01922c4d07fb`](https://github.com/Entif-AI/Bilqis-MLX/commit/01922c4d07fbab75d36c3d4c9fd7b27d8dbd9cce) `fix(bamf): bind active set to replayed Atlas source`
- [`c9f57c849ad2`](https://github.com/Entif-AI/Bilqis-MLX/commit/c9f57c849ad294fd9c77201b9d9078441952b35a) `docs(bamf): record generation zero r9 proof`
- [`a8193012ddc8`](https://github.com/Entif-AI/Bilqis-MLX/commit/a8193012ddc8758e500db0133c51321b8b4fa8fd) `fix(c09): preserve accepted training custody`
- [`def2f24b6d12`](https://github.com/Entif-AI/Bilqis-MLX/commit/def2f24b6d12ee0c47e158ecb8ec2c6919c07feb) `chore(bamf): checkpoint 516 acceptance-custody repair`
- [`ff00945aeccb`](https://github.com/Entif-AI/Bilqis-MLX/commit/ff00945aeccb2e6d479b6a9530dba0e3f41bb1b9) `fix(bamf): reject retained active-set drift`
- [`694ba90f55c1`](https://github.com/Entif-AI/Bilqis-MLX/commit/694ba90f55c1bc5fe1b98dc1cae19134d505947a) `test(bamf): bind long-history active set`
- [`e67ba0b3f3ba`](https://github.com/Entif-AI/Bilqis-MLX/commit/e67ba0b3f3baaf59daa735777243dd061aa391c8) `docs(bamf): record post-cap B13.5 pass`
- [`3e70b2c17b4f`](https://github.com/Entif-AI/Bilqis-MLX/commit/3e70b2c17b4fa9a243ea59a319279ba42dcc467d) `docs(bamf): record #697 PR turn-in`
- [`b52c9dd5f0a1`](https://github.com/Entif-AI/Bilqis-MLX/commit/b52c9dd5f0a1c1be8b47113a6b15fb81929001b7) `docs(bamf): mark #697 turned in`
- [`8be7f6be37ac`](https://github.com/Entif-AI/Bilqis-MLX/commit/8be7f6be37ac4472a8dffbad390cfd3de007f9e9) `fix(bamf): close accepted feature authority gaps`
- [`09b952b2fb7b`](https://github.com/Entif-AI/Bilqis-MLX/commit/09b952b2fb7ba686b85e0ef9b3cea59737206550) `Merge branch 'codex/bamf-unified-base-20261028' into codex/516-c09-1-egm-remediation-20261107`
- [`cce50961d68c`](https://github.com/Entif-AI/Bilqis-MLX/commit/cce50961d68c979b036986239f6f6a39b8c0f077) `fix(bamf): seal generation zero optimizer identity`
- [`f0c1356546de`](https://github.com/Entif-AI/Bilqis-MLX/commit/f0c1356546de58cb9350430ddc033df4ab306c29) `docs(bamf): preserve generation zero round 7 repair`
- [`5b7e5811dad9`](https://github.com/Entif-AI/Bilqis-MLX/commit/5b7e5811dad9e521796285217bcf5cb6e28c9fd1) `test(c09): expose atlas feature schema dependency gap`
- [`9c535f186b3f`](https://github.com/Entif-AI/Bilqis-MLX/commit/9c535f186b3fa9c2891f13110965c235e8ffe853) `fix(c09): bind atlas feature schema dependencies`
- [`210b29c275dd`](https://github.com/Entif-AI/Bilqis-MLX/commit/210b29c275dd912801cc85b2bc0aeb7e01c9e7f9) `fix(bamf): close C09.1 reverse dependency custody (#516)`
- [`7c38018b2c72`](https://github.com/Entif-AI/Bilqis-MLX/commit/7c38018b2c721017fa2d257db5e150803a462b7b) `docs(bamf): record 904 r10 proof pass`
- [`071519b6ea14`](https://github.com/Entif-AI/Bilqis-MLX/commit/071519b6ea141798fd37f4325b81c79f224a7cff) `fix(c09): index atlas feature materializer dependency`
- [`9d1bc1c8c753`](https://github.com/Entif-AI/Bilqis-MLX/commit/9d1bc1c8c753031f0642c60b0f85c8e2d0edb812) `chore(bamf): resume B13.3 on current unified`
- [`88d9548aedc8`](https://github.com/Entif-AI/Bilqis-MLX/commit/88d9548aedc8705b24c8f34107a3b73328907838) `docs(bamf): reconcile B13.3 current custody proof`
- [`56254f343904`](https://github.com/Entif-AI/Bilqis-MLX/commit/56254f343904cecebf7fa067e76a937836673083) `fix(c09): index atlas feature materializer dependency (#516)`
- [`86157d1cf981`](https://github.com/Entif-AI/Bilqis-MLX/commit/86157d1cf981dbbb78a02a1a78dc9186c92dbcd8) `docs(bamf): activate A13 four-time remediation`
- [`b20578b5f273`](https://github.com/Entif-AI/Bilqis-MLX/commit/b20578b5f273b0392f5e8da1c79ef50d4a8d51ce) `docs(bamf): repair B13.3 EGM readiness`
- [`711e227560d9`](https://github.com/Entif-AI/Bilqis-MLX/commit/711e227560d94e0ef654a35f669af1cff7b1a6ca) `fix(bamf): bind source-owned context time identity`
- [`5b025d55ed16`](https://github.com/Entif-AI/Bilqis-MLX/commit/5b025d55ed16c329e993b21f7feeed041caa7095) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/916-a13-four-time-context-20261108`
- [`93bf04c922da`](https://github.com/Entif-AI/Bilqis-MLX/commit/93bf04c922dae1a391c96308664e4e2f440bd841) `docs(bamf): activate C10 context requalification`
- [`be2a4eaf4c02`](https://github.com/Entif-AI/Bilqis-MLX/commit/be2a4eaf4c027ec45fab2f45e5b64f1b8d60fd4d) `docs(bamf): correct B13.3 pointer owner map`
- [`248b30e70d52`](https://github.com/Entif-AI/Bilqis-MLX/commit/248b30e70d52964363ed01d6fedf4ca15dacc0dd) `docs(bamf): inline B13.3 historical witness`
- [`254160a783ba`](https://github.com/Entif-AI/Bilqis-MLX/commit/254160a783ba7ceb81089fcf22732d15b0c1cb12) `fix(bamf): bind temporal identity into context invalidation`
- [`a39a4795bd9e`](https://github.com/Entif-AI/Bilqis-MLX/commit/a39a4795bd9eabb99f1fb89b23e0cdafecbc5075) `docs(bamf): record A13 typed temporal repair`
- [`326c443e2d79`](https://github.com/Entif-AI/Bilqis-MLX/commit/326c443e2d790ca23264cb9c5aa7135082bcf8e5) `fix(bamf): reject forged context time custody`
- [`42fe2110e4a2`](https://github.com/Entif-AI/Bilqis-MLX/commit/42fe2110e4a20ff5f6f652a4f9b69bc1629a0cea) `docs(bamf): record A13 custody hardening`
- [`5e822fb7fe71`](https://github.com/Entif-AI/Bilqis-MLX/commit/5e822fb7fe71941bd11f72cf80a6da85206e0896) `merge(bamf): integrate current unified for 904`
- [`d1ed9d928455`](https://github.com/Entif-AI/Bilqis-MLX/commit/d1ed9d9284554cc2495cff2564690a284dc3f636) `fix(c09): bind source authority to accepted run`
- [`577c70a6e8c9`](https://github.com/Entif-AI/Bilqis-MLX/commit/577c70a6e8c942d7a2200998bc34a29e99d9e1d2) `docs(bamf): turn in A13 four-time authority`
- [`1d579f78cb08`](https://github.com/Entif-AI/Bilqis-MLX/commit/1d579f78cb087fe937ef2d4bd20a35c4ccc8b981) `docs(bamf): refresh B13.3 child registry receipt`
- [`ec706edb96c6`](https://github.com/Entif-AI/Bilqis-MLX/commit/ec706edb96c6afc236383ee4a325d4e922dd3e47) `fix(bamf): project context requalification into C10`
- [`b2e87616b6d7`](https://github.com/Entif-AI/Bilqis-MLX/commit/b2e87616b6d72a9d67b9e324f8a006cebcdc63a5) `docs(bamf): checkpoint C10 context projection`
- [`bdcb13c85075`](https://github.com/Entif-AI/Bilqis-MLX/commit/bdcb13c8507564c0068a34c2c0640275ca85d4cb) `fix(bamf): bind source authority runtime to accepted run (#917 C09)`
- [`9795a3edff70`](https://github.com/Entif-AI/Bilqis-MLX/commit/9795a3edff705ff6e44eec29dc60fed74d2abc74) `fix(bamf): bind source-owned context temporal identity`
- [`b7f493282abe`](https://github.com/Entif-AI/Bilqis-MLX/commit/b7f493282abee062ed0f343c4eab10bb575c3b26) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/480-b13-3-reconcile-20261108`
- [`5eb62d5e5e16`](https://github.com/Entif-AI/Bilqis-MLX/commit/5eb62d5e5e16fbdf15ac0d715b17fe29ec545c34) `docs(bamf): merge-forward B13.3 proof basis`
- [`ef28afab22e2`](https://github.com/Entif-AI/Bilqis-MLX/commit/ef28afab22e26ab5d5d0c0c3cea6d3b73d659d36) `docs(bamf): bind merge-forwarded B13.3 witnesses`
- [`afe3947d1b5c`](https://github.com/Entif-AI/Bilqis-MLX/commit/afe3947d1b5c49590cb25e107e5238ba281487e2) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/911-c10-context-requalification-20261108`
- [`b6422871764c`](https://github.com/Entif-AI/Bilqis-MLX/commit/b6422871764c4a979684afb4faa09db914647f61) `docs(bamf): record B13.3 test evidence reuse`
- [`11d796c68835`](https://github.com/Entif-AI/Bilqis-MLX/commit/11d796c688350139802fe249e3944e77f4bb6de8) `fix(bamf): consume typed context requalification custody`
- [`6908e3f859a8`](https://github.com/Entif-AI/Bilqis-MLX/commit/6908e3f859a81c4173cdf686e2c87eafdc810f31) `docs(bamf): checkpoint typed C10 context projection`
- [`89b9e463a02c`](https://github.com/Entif-AI/Bilqis-MLX/commit/89b9e463a02c1c89fee0e717165361059497509b) `test(bamf): freeze context temporal fixture`
- [`d4879ff723d6`](https://github.com/Entif-AI/Bilqis-MLX/commit/d4879ff723d6a4495cc1c307468c748a2e1ce6bb) `docs(bamf): turn in B13.3`
- [`81a9e4e24fcc`](https://github.com/Entif-AI/Bilqis-MLX/commit/81a9e4e24fcca307cb0019db4e4c07737a8b744b) `feat(bamf): separate disposable caches from historical v1 reader custody (#480 / B13.3)`
- [`ae0b131817bc`](https://github.com/Entif-AI/Bilqis-MLX/commit/ae0b131817bcd1b7379ae38826d6d875ae4d2ef6) `fix(bamf): bind context projection to pending C09 task`
- [`0b9b140e3542`](https://github.com/Entif-AI/Bilqis-MLX/commit/0b9b140e3542cefc77dc3b1215d518a8cdc9c0b2) `docs(bamf): record Reno 911 EGM round 1 repair`
- [`a96ed2c0211f`](https://github.com/Entif-AI/Bilqis-MLX/commit/a96ed2c0211f219000966e192fb36d554601f2f4) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/911-c10-context-requalification-20261108`
- [`dbb9ba007244`](https://github.com/Entif-AI/Bilqis-MLX/commit/dbb9ba00724454d570f73b3e68d8d4d32b37fd98) `docs(bamf): sync Reno 911 after B13.3 landing`
- [`5f40f2c90520`](https://github.com/Entif-AI/Bilqis-MLX/commit/5f40f2c90520741a252faad2c2f0dbe8625f1c63) `docs(bamf): turn in Reno 911`
- [`15f02c2cfef2`](https://github.com/Entif-AI/Bilqis-MLX/commit/15f02c2cfef26d5370d10e6446592e00caf7bc65) `fix(runtime): anchor source authority to accepted B13 custody`
- [`b028c89a08f0`](https://github.com/Entif-AI/Bilqis-MLX/commit/b028c89a08f06cd36000aa2e44a29c4e6123b8ad) `fix(c10): project context requalification from accepted custody (#911)`
- [`1e430b876982`](https://github.com/Entif-AI/Bilqis-MLX/commit/1e430b876982108573371bd62c8fd2877edc5665) `refactor(bamf): split generation publication custody`
- [`2277676d9310`](https://github.com/Entif-AI/Bilqis-MLX/commit/2277676d931054d7746c09fa67c3de095967764c) `fix(bamf): seal generation zero retry authority`
- [`a767d89914c3`](https://github.com/Entif-AI/Bilqis-MLX/commit/a767d89914c349f0cde79a69f615b5a6a58a366e) `refactor(bamf): group custody publication modules`
- [`4b0e719639e1`](https://github.com/Entif-AI/Bilqis-MLX/commit/4b0e719639e14178bf6c442b4f256030fa6de2c1) `refactor(bamf): group custody contract tests`
- [`1bc7e27ec0f5`](https://github.com/Entif-AI/Bilqis-MLX/commit/1bc7e27ec0f55227f42321a60a39b3c5dc63f45a) `refactor(bamf): group custody publication tests`
- [`e1facbf4dc93`](https://github.com/Entif-AI/Bilqis-MLX/commit/e1facbf4dc93749acbed3be71a6ef5cde2605b82) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/917-c09-source-authority-runtime-r3-20261108`
- [`3ffa350f67b4`](https://github.com/Entif-AI/Bilqis-MLX/commit/3ffa350f67b4496d8c7c9d74cd68c7822c35e96f) `test(c09): align context projection with owner-bound authority`
- [`b4ff8ea8f989`](https://github.com/Entif-AI/Bilqis-MLX/commit/b4ff8ea8f989d1d65a49a040a0fc8d90031a686a) `fix(bamf): bind source authority to accepted run custody after EGM (C09)`
- [`228d9b52aa55`](https://github.com/Entif-AI/Bilqis-MLX/commit/228d9b52aa55297b52762165ea2741a6bac52349) `merge(bamf): consume unified genesis authority for #926`
- [`6791610f87fd`](https://github.com/Entif-AI/Bilqis-MLX/commit/6791610f87fdc5234928806ae69c42d68d967e50) `chore(bamf): preserve trainer authority in unified sync`
- [`cbbce2e487c4`](https://github.com/Entif-AI/Bilqis-MLX/commit/cbbce2e487c4bb6df033625ad7c626d8229efca6) `fix(c09): close accepted-run authority bypasses after EGM`
- [`ec87edac08a7`](https://github.com/Entif-AI/Bilqis-MLX/commit/ec87edac08a7f43b5fa44ff9278d0f0b2b91e855) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/917-c09-source-authority-runtime-r3-20261108`
- [`e8d183e25fa7`](https://github.com/Entif-AI/Bilqis-MLX/commit/e8d183e25fa79969486b8aac19520cfce6c9e7f6) `fix(c09): root accepted authority in host custody`
- [`aac69aedbdf4`](https://github.com/Entif-AI/Bilqis-MLX/commit/aac69aedbdf40276a70745a14bbcf32ddb67dcd7) `test(c09): keep authority forgery proof catalog-clean`
- [`a4684fc7e063`](https://github.com/Entif-AI/Bilqis-MLX/commit/a4684fc7e063f724adba0f07fe79953acfe2ed66) `fix(bamf): reconcile genesis retry delivery (#925)`
- [`346d7391567a`](https://github.com/Entif-AI/Bilqis-MLX/commit/346d7391567a8c6f50bd2ed26e89bc07828edb88) `fix(bamf): revalidate genesis authority at commit`
- [`b1a33ee3099a`](https://github.com/Entif-AI/Bilqis-MLX/commit/b1a33ee3099a9121117ccd522f7f2e36979242b4) `Fix generation-zero cold trust root (#923)`
- [`200441d3dbc2`](https://github.com/Entif-AI/Bilqis-MLX/commit/200441d3dbc27221fd2d77a1c6d14a1a5360d1a8) `fix(bamf): close accepted authority custody gaps (C09)`
- [`fef324b4a353`](https://github.com/Entif-AI/Bilqis-MLX/commit/fef324b4a3538ee804318857c777c12fc60dd606) `Merge commit 'b1a33ee3099a9121117ccd522f7f2e36979242b4' into codex/904-egm-mitigations-integrated-20261108`
- [`25739fb7516e`](https://github.com/Entif-AI/Bilqis-MLX/commit/25739fb7516ed1a58ee3f9fc9eb16a87ffd784c5) `Merge commit '346d7391567a8c6f50bd2ed26e89bc07828edb88' into codex/904-egm-mitigations-integrated-20261108`
- [`5cb7d6b01f0a`](https://github.com/Entif-AI/Bilqis-MLX/commit/5cb7d6b01f0a74952673efa046fecea9d21d6783) `Merge commit 'a4684fc7e063f724adba0f07fe79953acfe2ed66' into codex/904-egm-mitigations-integrated-20261108`
- [`cd20336ef874`](https://github.com/Entif-AI/Bilqis-MLX/commit/cd20336ef8747d86a831ce09487522892affd79b) `fix(bamf): seal accepted authority replay and leases (C09)`
- [`65759ae2461c`](https://github.com/Entif-AI/Bilqis-MLX/commit/65759ae2461c661c22dc55ba157bb6ef91b3f888) `fix(bamf): harden generation zero cold trust`
- [`112812ef3df6`](https://github.com/Entif-AI/Bilqis-MLX/commit/112812ef3df65d857035505390e5fca39c75610d) `fix(bamf): bind genesis bootstrap to full identity (#928)`
- [`27406019063e`](https://github.com/Entif-AI/Bilqis-MLX/commit/27406019063e25bc27a015f5c91fb94ee61af06f) `docs(bamf): separate EGM design review from implementation proof`
- [`20b53ea3065c`](https://github.com/Entif-AI/Bilqis-MLX/commit/20b53ea3065cf3bea8f85d47b32f02704e29d64e) `docs(bamf): record design verification lifecycle ADR`
- [`eaad386baeb4`](https://github.com/Entif-AI/Bilqis-MLX/commit/eaad386baeb48f5b9a8d9c6efdcaea8054ce28db) `docs(bamf): process lifecycle constitutional amendments 20261108 (ADR-136)`
- [`1b7e3d090aed`](https://github.com/Entif-AI/Bilqis-MLX/commit/1b7e3d090aed701ba8ded761d6f1ceabd1f553dd) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/904-egm-mitigations-integrated-20261108`
- [`abdc075f1be1`](https://github.com/Entif-AI/Bilqis-MLX/commit/abdc075f1be18ca08c2492b5e59ab3bea075583a) `test(bamf): derive registry counts per branch`
- [`82b9c9e11c6f`](https://github.com/Entif-AI/Bilqis-MLX/commit/82b9c9e11c6fcd670b514dce2b5264487edae59f) `test(bamf): align downstream fixtures with genesis lifecycle`
- [`22ec172f2fc9`](https://github.com/Entif-AI/Bilqis-MLX/commit/22ec172f2fc9fa1985b704637b1b3f8a649b4871) `refactor(bamf): clear changed-file hygiene gate`
- [`8c6a99a2316a`](https://github.com/Entif-AI/Bilqis-MLX/commit/8c6a99a2316a992faecd163d58ce04301ef129f3) `fix(bamf): align integration fixtures with genesis lifecycle`
- [`6838afba6094`](https://github.com/Entif-AI/Bilqis-MLX/commit/6838afba6094339e09ea4d5c3df1a991d13a7465) `test(bamf): split adoption suite for portable gate`
- [`6c9d796cbecf`](https://github.com/Entif-AI/Bilqis-MLX/commit/6c9d796cbecf84081e91f71cf493876c47ff6949) `style(bamf): normalize adoption test eof`
- [`7d9e0e8209e2`](https://github.com/Entif-AI/Bilqis-MLX/commit/7d9e0e8209e2d077e4fc30f65a3ebf3f29a91f3f) `feat(bamf): publish authenticated generation-zero custody (#904)`
- [`63d61f81affe`](https://github.com/Entif-AI/Bilqis-MLX/commit/63d61f81affeb87aed6cc41d8609976d6f582716) `docs(bamf): reactivate C03 after B13.6`
- [`f37349ce7386`](https://github.com/Entif-AI/Bilqis-MLX/commit/f37349ce7386662e1f0b1dc2872f8a8090392b96) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/bamf02-c03-376-20261107`
- [`c756210cd04e`](https://github.com/Entif-AI/Bilqis-MLX/commit/c756210cd04e4f628802de0a5c7a84b6838986c1) `chore(bamf): reactivate #510 after authority unlock`
- [`5153a11141bf`](https://github.com/Entif-AI/Bilqis-MLX/commit/5153a11141bf83b2684c12553e89821c8c868502) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/510-c07-atomic-adoption-20261107`
- [`db790df2b7b1`](https://github.com/Entif-AI/Bilqis-MLX/commit/db790df2b7b12e53172805847a1e696c36a68cdc) `fix(c07): bind staged candidate to accepted B13 parent`
- [`00e5f5720c89`](https://github.com/Entif-AI/Bilqis-MLX/commit/00e5f5720c89b6fab95f57fea8065c9e8fbfe709) `chore(bamf): park #510 on accepted-run bridge`
- [`b5603ebe2587`](https://github.com/Entif-AI/Bilqis-MLX/commit/b5603ebe2587521bc0eb556904435a5006711e8a) `feat(bamf): bind C03 visits to accepted custody`
- [`66d775203276`](https://github.com/Entif-AI/Bilqis-MLX/commit/66d775203276f5eecf21f1e55fda1e0bb5a617e7) `docs(bamf): record C03 accepted-custody qualification`
- [`0072d962f4f6`](https://github.com/Entif-AI/Bilqis-MLX/commit/0072d962f4f6a9dfcbac996353af10acbaf0ce39) `fix(c09): seal accepted authority ownership after EGM`
- [`fd6aaa9fd551`](https://github.com/Entif-AI/Bilqis-MLX/commit/fd6aaa9fd5517f206a16bd2aa3069975611b5709) `docs(bamf): turn in C03 after fresh EGM`
- [`41d546307538`](https://github.com/Entif-AI/Bilqis-MLX/commit/41d5463075383a63969f6a6d82df6cf3bd4c8eda) `docs(bamf): bind C03 turn-in to PR 932`
- [`874eabc39ad2`](https://github.com/Entif-AI/Bilqis-MLX/commit/874eabc39ad2086b758e891ccf9b6f6a2f11ccec) `fix(bamf): name C03 digest guard widths`
- [`caf22bbc02c9`](https://github.com/Entif-AI/Bilqis-MLX/commit/caf22bbc02c99d59a46c9f0561c508fe00e8f801) `docs(bamf): record C03 hosted CI re-audit`
- [`a834bfa2de18`](https://github.com/Entif-AI/Bilqis-MLX/commit/a834bfa2de183ca7e33c6c0b46326cfcfb5e5b0f) `Implement BAMF first-student foundation preflight`
- [`2c26d4aca90f`](https://github.com/Entif-AI/Bilqis-MLX/commit/2c26d4aca90f275e1c255aa6a197ab63e0528480) `feat(bamf): carry C03 teacher through accepted custody`
- [`c087191a0643`](https://github.com/Entif-AI/Bilqis-MLX/commit/c087191a0643c3e8fdf00119b63c6d07dd58962f) `Finish BAMF first-student launch contract`
- [`9ec67153debe`](https://github.com/Entif-AI/Bilqis-MLX/commit/9ec67153debeea705f57b94150a3f61b6f588cab) `Turn in BAMF C16.1b flow control`
- [`3cf68315e5a4`](https://github.com/Entif-AI/Bilqis-MLX/commit/3cf68315e5a44535ac815b119849cb3c039527be) `Revert "Turn in BAMF C16.1b flow control"`
- [`66b8133800d6`](https://github.com/Entif-AI/Bilqis-MLX/commit/66b8133800d65f7310bea2de4c17bd446d50dede) `merge(bamf): consume generation-zero custody in C09 remediation`
- [`d310f9643212`](https://github.com/Entif-AI/Bilqis-MLX/commit/d310f9643212a1d45768368577124a895cdbe4c8) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/917-c09-source-authority-runtime-r3-20261108`
- [`0c27e3ed9572`](https://github.com/Entif-AI/Bilqis-MLX/commit/0c27e3ed95721e9b288374dc5a659aaa1a4165e1) `Reject BAMF target overlap with source run`
- [`c19393f495fe`](https://github.com/Entif-AI/Bilqis-MLX/commit/c19393f495fe30e0b9cadc9feef703685941dd07) `Harden BAMF first-student preflight custody`
- [`f5466e1e60e5`](https://github.com/Entif-AI/Bilqis-MLX/commit/f5466e1e60e59a95d76cc786a0c6b1a961c7c05a) `test(c09): align repaired authority fixtures with genesis custody`
- [`338303eadb9f`](https://github.com/Entif-AI/Bilqis-MLX/commit/338303eadb9f95a8bde608e8214d0bbd6f2d30b8) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/543-c16-foundation-20261108`
- [`b05873bb3ddf`](https://github.com/Entif-AI/Bilqis-MLX/commit/b05873bb3ddf2d64c8960ea03ef6052a0d6a8bfa) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/905-c02-5-visit-provenance-20261107`
- [`d76063fd2a79`](https://github.com/Entif-AI/Bilqis-MLX/commit/d76063fd2a79cfd0d15aba8f1eeb87a15828bce1) `docs(bamf): qualify C02.5 after parent integration`
- [`f7e153ebfab0`](https://github.com/Entif-AI/Bilqis-MLX/commit/f7e153ebfab0d4fdf6b383d9e8ee1e68f269587d) `Route BAMF dashboard through runtime projection`
- [`e78e44a6bafa`](https://github.com/Entif-AI/Bilqis-MLX/commit/e78e44a6bafa6c078f039b902254e48bfe01ba4b) `test(bamf): close C02.5 provenance proof gap`
- [`26695dda6f73`](https://github.com/Entif-AI/Bilqis-MLX/commit/26695dda6f7367320cd8a5d44a313c1aa5ad6fda) `docs(bamf): record C02.5 turn-in EGM`
- [`12f2a29b1dae`](https://github.com/Entif-AI/Bilqis-MLX/commit/12f2a29b1daeebd0c8b024f6fa875f0ce7645188) `docs(bamf): bind C02.5 EGM to legacy authority`
- [`fd1ed861b781`](https://github.com/Entif-AI/Bilqis-MLX/commit/fd1ed861b78125141183fd42e1286c87581c6914) `Refactor BAMF foundation proof test`
- [`f0409d0ddaae`](https://github.com/Entif-AI/Bilqis-MLX/commit/f0409d0ddaaec8bef4c6fd3c0b198b6877123e13) `Keep BAMF CLI inspection MLX-free`
- [`7b9ec1aaaf03`](https://github.com/Entif-AI/Bilqis-MLX/commit/7b9ec1aaaf031cb32357847f8df25f960527374a) `Make BAMF foundation test xdist-safe`
- [`4702ea6c59f8`](https://github.com/Entif-AI/Bilqis-MLX/commit/4702ea6c59f81e750e8114f5919049130328cc9a) `fix(c09): keep accepted correction custody process-owned`
- [`f0ef0dd3d8b5`](https://github.com/Entif-AI/Bilqis-MLX/commit/f0ef0dd3d8b560ad9fc82c2570053ab9f67251b6) `Turn in BAMF C16.1b`
- [`c410b6d39094`](https://github.com/Entif-AI/Bilqis-MLX/commit/c410b6d39094eb71070238146223afb47efa788b) `Split BAMF foundation test fixture`
- [`f4686d121179`](https://github.com/Entif-AI/Bilqis-MLX/commit/f4686d1211790130e7cc0296aceddd7a5e60bdd1) `refactor(c09): bound accepted owner custody helpers`
- [`8d2d6f798a34`](https://github.com/Entif-AI/Bilqis-MLX/commit/8d2d6f798a344f1f24117e717deb9695b62afc3f) `feat(bamf): bind C16.1b fresh student foundation (#543 / PR #933)`
- [`be4fd966ab63`](https://github.com/Entif-AI/Bilqis-MLX/commit/be4fd966ab63a965c2a72d52ce6e59acb06354cb) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/917-c09-source-authority-runtime-r3-20261108`
- [`fb8c2afd6e6f`](https://github.com/Entif-AI/Bilqis-MLX/commit/fb8c2afd6e6faf9a63d66620311edd101ee5946b) `Track C09 remediation flow state`
- [`c80277d75633`](https://github.com/Entif-AI/Bilqis-MLX/commit/c80277d756332fc8d022c876deada05005c8fd49) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/917-c09-source-authority-runtime-r3-20261108`
- [`828042ce96e8`](https://github.com/Entif-AI/Bilqis-MLX/commit/828042ce96e8e7094febb7196ac9cd4c847de6eb) `test(c09): assert fail-closed cache publication race`
- [`7b7cf7ea8eca`](https://github.com/Entif-AI/Bilqis-MLX/commit/7b7cf7ea8eca6b01938d68ed458ee3a8174405d8) `test(bamf): close C02.5 premerge compatibility`
- [`61643a6200b8`](https://github.com/Entif-AI/Bilqis-MLX/commit/61643a6200b8c0acdb95ff95de295bfa0a792653) `Merge remote-tracking branch 'origin/codex/917-c09-source-authority-runtime-r3-20261108' into codex/917-c09-source-authority-runtime-r3-20261108`
- [`c87f67544e4a`](https://github.com/Entif-AI/Bilqis-MLX/commit/c87f67544e4a519566e52825cf6d14811f875ccd) `test(c09): enter cache fixtures through B13 genesis`
- [`51110dedd458`](https://github.com/Entif-AI/Bilqis-MLX/commit/51110dedd4588e4238f749dab05e40b10357651a) `docs(bamf): record C02.5 exact-head turn-in proof`
- [`b6232012fd58`](https://github.com/Entif-AI/Bilqis-MLX/commit/b6232012fd5813bc9902492f3e47c44fd3c2c2b3) `Merge remote-tracking branch 'origin/codex/917-c09-source-authority-runtime-r3-20261108' into codex/917-c09-source-authority-runtime-r3-20261108`
- [`a5a2212862c2`](https://github.com/Entif-AI/Bilqis-MLX/commit/a5a2212862c29b45e84c02a73ca4c82f1f7698fa) `docs(bamf): turn in C02.5 for human review`
- [`ee43c7246def`](https://github.com/Entif-AI/Bilqis-MLX/commit/ee43c7246def7627ef58e9b017aaaea4cb21bbc5) `docs(bamf): reconcile Lane C turn-in ledger`
- [`4bfcbd5a9aaa`](https://github.com/Entif-AI/Bilqis-MLX/commit/4bfcbd5a9aaa22a1bc2bca4c7a64ec203df07044) `feat(bamf): transport accepted run and visit provenance (#905)`
- [`dab608fc9c22`](https://github.com/Entif-AI/Bilqis-MLX/commit/dab608fc9c227732166c354ad5e35b010112bfd5) `docs(bamf): resume C07 adoption after C16 foundation`
- [`5209c230f67c`](https://github.com/Entif-AI/Bilqis-MLX/commit/5209c230f67cd55ed4e919fe62bc954b665d306b) `fix(c09): fail closed across accepted runtime reset`
- [`db5ba4a9c429`](https://github.com/Entif-AI/Bilqis-MLX/commit/db5ba4a9c429ebf4fe4ae34ebce8c06ca49293fe) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/510-c07-atomic-adoption-20261107`
- [`6df4258d55ce`](https://github.com/Entif-AI/Bilqis-MLX/commit/6df4258d55cea1ac9df0e09622e0fbb035f7ecc3) `chore(bamf): record C09 failed EGM repair head`
- [`b9e3e24b398a`](https://github.com/Entif-AI/Bilqis-MLX/commit/b9e3e24b398abc0c5df9938c6e0ebe28ff919390) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/917-c09-source-authority-runtime-r3-20261108`
- [`65ef68856b85`](https://github.com/Entif-AI/Bilqis-MLX/commit/65ef68856b8501899f6f0405deeb32166a82f5ff) `chore(bamf): sync C09 flow receipt to reviewed unified`
- [`d4e67cc9c4c4`](https://github.com/Entif-AI/Bilqis-MLX/commit/d4e67cc9c4c4f65eba3541f4203544cc815b37e9) `Merge reviewed unified for B10 request disposition`
- [`31be2acb53e7`](https://github.com/Entif-AI/Bilqis-MLX/commit/31be2acb53e7e8d14779b45602bc7d9ae4741ffd) `docs(bamf): qualify B10 disposition on current unified`
- [`50c6215f09dc`](https://github.com/Entif-AI/Bilqis-MLX/commit/50c6215f09dcc312ac21e657384369bbedc2439e) `test(c09): align capability custody assertion`
- [`55e94b298e44`](https://github.com/Entif-AI/Bilqis-MLX/commit/55e94b298e4480f3eb4f4886568db10b7f36809e) `Merge reviewed unified for A13 prefix authority`
- [`fba3ecb2b9ab`](https://github.com/Entif-AI/Bilqis-MLX/commit/fba3ecb2b9abdc3c3eacc45b5e890ceef7f60d4b) `docs(bamf): qualify A13 prefix authority on current unified`
- [`d7c018e6acb9`](https://github.com/Entif-AI/Bilqis-MLX/commit/d7c018e6acb9e2365d2bbf1af04c9efd098fb6b5) `Merge reviewed unified for C05 evaluation custody`
- [`c31c4b9c2316`](https://github.com/Entif-AI/Bilqis-MLX/commit/c31c4b9c23163f20cf2127383524df7f231b6283) `fix(c09): close accepted authority mutation races`
- [`26dd37c74a1b`](https://github.com/Entif-AI/Bilqis-MLX/commit/26dd37c74a1b8ff5f6effdcc9279eeace1b335b0) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/917-c09-source-authority-runtime-r3-20261108`
- [`c6dcc8cd30f6`](https://github.com/Entif-AI/Bilqis-MLX/commit/c6dcc8cd30f626b4b53d8b110f915c3cc481f5b1) `docs(bamf): qualify C05 evaluation custody on current unified`
- [`08af50003a30`](https://github.com/Entif-AI/Bilqis-MLX/commit/08af50003a3019c3aa9d24f454b1bd47f2a63e49) `Merge remote-tracking branch 'origin/codex/917-c09-source-authority-runtime-r3-20261108' into codex/917-c09-source-authority-runtime-r3-20261108`
- [`37417f9e8092`](https://github.com/Entif-AI/Bilqis-MLX/commit/37417f9e80921e0b9be040eaf48da8f0940e8ed9) `fix(bamf): bind split refinement contracts to A05 prefix identity`
- [`c956380f20d3`](https://github.com/Entif-AI/Bilqis-MLX/commit/c956380f20d3efbec4df7c12831a0a9bce2c4c36) `docs(bamf): bind A13 review repair receipt`
- [`852382350939`](https://github.com/Entif-AI/Bilqis-MLX/commit/8523823509393f80c6125e61297c486f1d78b7e9) `docs(bamf): record B10 merge-readiness review`
- [`605494e69964`](https://github.com/Entif-AI/Bilqis-MLX/commit/605494e69964c597c0e082715dc9c130f5e2f343) `docs(bamf): turn in B10 request disposition`
- [`fc3a32f59f2f`](https://github.com/Entif-AI/Bilqis-MLX/commit/fc3a32f59f2f77eb352d586a3b43ddff1d2a0c53) `docs(bamf): record A13 repaired-head review pass`
- [`efcaf2d4578c`](https://github.com/Entif-AI/Bilqis-MLX/commit/efcaf2d4578cc491b0be9e2d9a44574193537110) `docs(bamf): turn in A13 prefix authority`
- [`896ca89541d1`](https://github.com/Entif-AI/Bilqis-MLX/commit/896ca89541d1ec75bc6589a5797e78e00967081c) `test(c09): use accepted host for cold history`
- [`c69dc4b9066f`](https://github.com/Entif-AI/Bilqis-MLX/commit/c69dc4b9066f6312d3ce5bdf0833981adff18dd5) `docs(bamf): record C05 merge-readiness review`
- [`8e319a227ab1`](https://github.com/Entif-AI/Bilqis-MLX/commit/8e319a227ab1372b5c2f998a678875d34ba71f84) `docs(bamf): turn in C05 evaluation custody`
- [`b86dd279c6cd`](https://github.com/Entif-AI/Bilqis-MLX/commit/b86dd279c6cd70d55204f582387437a3c5c2533e) `fix(bamf): close post-merge accepted-authority bypasses (C09 / PR #927 / #917)`
- [`7f55e4780d28`](https://github.com/Entif-AI/Bilqis-MLX/commit/7f55e4780d2808bd8444d145721bfb5e2dcebd57) `fix(bamf): integrate B10 refinement request disposition`
- [`5f87cc7e1d31`](https://github.com/Entif-AI/Bilqis-MLX/commit/5f87cc7e1d315f11f8409bee583584cf155f469c) `fix(bamf): integrate A13 compiled-prefix authority`
- [`fcf069a78fbb`](https://github.com/Entif-AI/Bilqis-MLX/commit/fcf069a78fbb4d2c041e1af0d85814bbbaf038c3) `Merge branch 'codex/bamf-unified-base-20261028' into codex/378-c05-eval-ast-20261107`
- [`9385ac7f336d`](https://github.com/Entif-AI/Bilqis-MLX/commit/9385ac7f336dca090cdd746fe8b87904ff2e5415) `fix(bamf): integrate C05 evaluation source custody`
- [`87f9edb64b6e`](https://github.com/Entif-AI/Bilqis-MLX/commit/87f9edb64b6e955f3d0490af1eee1220435bc639) `feat(bamf): bind C07 native adoption authority`
- [`5fa11a422022`](https://github.com/Entif-AI/Bilqis-MLX/commit/5fa11a422022efbc9f799391e1880b2d66fbc2a9) `chore(bamf): activate B11.1 composition`
- [`29054e32a3b1`](https://github.com/Entif-AI/Bilqis-MLX/commit/29054e32a3b17897748125ecac9370f77cdd46e6) `chore(bamf): reactivate A02 production staging`
- [`98eb72dd872b`](https://github.com/Entif-AI/Bilqis-MLX/commit/98eb72dd872b817945260bd0ff344238fac9b1b7) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/bamf02-a-399-production-admission-20261106`
- [`93940f929ca4`](https://github.com/Entif-AI/Bilqis-MLX/commit/93940f929ca4395e926bfdfe600cdeee5e7e580e) `fix(bamf): carry refinement authority into B11`
- [`28cf45396c21`](https://github.com/Entif-AI/Bilqis-MLX/commit/28cf45396c21b6e77d887dfbe01a5f995907fa2e) `fix(bamf): seal A02 staged handoff authority`
- [`84e8c9004148`](https://github.com/Entif-AI/Bilqis-MLX/commit/84e8c9004148bc80c69af670feec4490adf68826) `test(bamf): bind A02 active-set growth to C07`
- [`08078e6658c6`](https://github.com/Entif-AI/Bilqis-MLX/commit/08078e6658c6ea6fec00e19f97c02cb8527becde) `docs(bamf): park A02 on reviewed C07 handoff`
- [`bbba88ebb4ce`](https://github.com/Entif-AI/Bilqis-MLX/commit/bbba88ebb4cef90e62267c1b7ce3f00721d71817) `fix(c09): preserve packed frame context views`
- [`68a59828a5c1`](https://github.com/Entif-AI/Bilqis-MLX/commit/68a59828a5c16c423bd5e0b25e46ed2af129113a) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/510-c07-atomic-adoption-20261107`
- [`5d43f945512e`](https://github.com/Entif-AI/Bilqis-MLX/commit/5d43f945512e9af5347154d90f66b611bf1e37a4) `feat(bamf): compose B11 local refinement`
- [`33db587838f7`](https://github.com/Entif-AI/Bilqis-MLX/commit/33db587838f783c6db38d3e7dd7ad69b251fdb18) `fix(bamf): preserve C07 replay through source custody sync`
- [`e05256ded245`](https://github.com/Entif-AI/Bilqis-MLX/commit/e05256ded2454bf8e03674f0d64b0734bbe5e1f3) `test(c09): close multi-context readiness proof gaps`
- [`6de274481fb9`](https://github.com/Entif-AI/Bilqis-MLX/commit/6de274481fb9654b6f4b7c4599538d81f7e667b3) `fix(bamf): bind A02 staging to accepted run seed`
- [`b9310c6d8d7c`](https://github.com/Entif-AI/Bilqis-MLX/commit/b9310c6d8d7c92d65ef43f61c4830f9644fab984) `fix(bamf): bind B11 refinement to task authority`
- [`f0faed7f62b7`](https://github.com/Entif-AI/Bilqis-MLX/commit/f0faed7f62b71d2a3b21a81931635e9a88249f4f) `test(c09): split context-view regressions`
- [`27afb804ae2e`](https://github.com/Entif-AI/Bilqis-MLX/commit/27afb804ae2eb6e1770a64d46600637f9c6dd2af) `docs(bamf): track c09 context-view review state`
- [`37ed2a94276a`](https://github.com/Entif-AI/Bilqis-MLX/commit/37ed2a94276af0df3e9033f2d6e4d9711a212748) `fix(bamf): stage A02 from accepted feature lineage`
- [`6b5aef0a7c79`](https://github.com/Entif-AI/Bilqis-MLX/commit/6b5aef0a7c798bc3b5b77ddbb930725e19ff93eb) `fix(c09): rematerialize drifted motif custody`
- [`743d8d825d46`](https://github.com/Entif-AI/Bilqis-MLX/commit/743d8d825d46a23c0f3ac2bb3df4bbd9540d993a) `fix(bamf): bind C07 retries to accepted authority`
- [`e11c334055e5`](https://github.com/Entif-AI/Bilqis-MLX/commit/e11c334055e5a5e0934888bdb6f253325f961dc0) `docs(bamf): record c09 rematerialization repair`
- [`aa8c08d9b437`](https://github.com/Entif-AI/Bilqis-MLX/commit/aa8c08d9b4373d48151cad8a2205a88c0801752d) `fix(bamf): persist C07 factory release before B13 commit`
- [`636ac8ffdeec`](https://github.com/Entif-AI/Bilqis-MLX/commit/636ac8ffdeece7d6f8b24e9d1f46596396848db7) `fix(bamf): preserve packed frame context views (#930 / C09 / PR #938)`
- [`2fc317bead1c`](https://github.com/Entif-AI/Bilqis-MLX/commit/2fc317bead1c94b3d389ab06109f515db58a307d) `test(bamf): observe durable factory handoff before B13`
- [`587bb61e0788`](https://github.com/Entif-AI/Bilqis-MLX/commit/587bb61e07885cafd356329ad8b6db15bce4c3f9) `fix(bamf): bind native C07 factory authority to B13`
- [`5f37d7056157`](https://github.com/Entif-AI/Bilqis-MLX/commit/5f37d70561570f9bc0560c0e5c5a1649bcd7397e) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/510-c07-atomic-adoption-20261107`
- [`6c59b20230ba`](https://github.com/Entif-AI/Bilqis-MLX/commit/6c59b20230ba222cfbd24933c1de046b558aceb2) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/bamf02-a-399-production-admission-20261106`
- [`115489c2d608`](https://github.com/Entif-AI/Bilqis-MLX/commit/115489c2d608f5408c7585a31cdc5b23891f89a5) `docs(bamf): qualify A02 on current unified`
- [`19988b8101f6`](https://github.com/Entif-AI/Bilqis-MLX/commit/19988b8101f68d3d33153dd4fb99be25bd3fdb63) `docs(bamf): reactivate c12 authority remediation`
- [`90aef8e92610`](https://github.com/Entif-AI/Bilqis-MLX/commit/90aef8e926101016740e5e55f6d8eff82ce13d52) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/bamf02-c12-526-exchange-20261101`
- [`7cf50839300a`](https://github.com/Entif-AI/Bilqis-MLX/commit/7cf50839300a4d4377694d28e817b4476875568d) `fix(bamf): close A02 accepted feature replay seam`
- [`f85c65707614`](https://github.com/Entif-AI/Bilqis-MLX/commit/f85c65707614e9e96e3fd360feeadc298ffb4087) `test(c12): close source-rights authority proof`
- [`f31a8a19626c`](https://github.com/Entif-AI/Bilqis-MLX/commit/f31a8a19626c4bddbd274a60bc33abae13807b74) `docs(bamf): bind c12 final review candidate`
- [`26bcc2657e20`](https://github.com/Entif-AI/Bilqis-MLX/commit/26bcc2657e20d231ec9a6692b57d2c75b182d7a7) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/bamf02-b-neural`
- [`dac1b7117010`](https://github.com/Entif-AI/Bilqis-MLX/commit/dac1b71170106e2c210f0b9cd9342c2d36779bf5) `refactor(bamf): expose A02 feature replay owner seams`
- [`e5cd3bbce94c`](https://github.com/Entif-AI/Bilqis-MLX/commit/e5cd3bbce94ceb09cd006ade67274e0db38a0bf5) `refactor(bamf): split A02 staging orchestration`
- [`5311e6685398`](https://github.com/Entif-AI/Bilqis-MLX/commit/5311e66853988e60485df12d88ce4752f366b6a0) `fix(c12): authenticate retention publication authority`
- [`8899f7d2cf0c`](https://github.com/Entif-AI/Bilqis-MLX/commit/8899f7d2cf0c4c89b992d9fdc72242944d7531c2) `feat(bamf): assemble atlas-native forward and refinement (B11.1 / PR #939 / #471)`
- [`eaf3bbe0bba2`](https://github.com/Entif-AI/Bilqis-MLX/commit/eaf3bbe0bba2263a1a14fda3891a7e78d1d2ed87) `docs(bamf): record c12 authority repair`
- [`402295808906`](https://github.com/Entif-AI/Bilqis-MLX/commit/402295808906cf69fd20d929f02becec778edcb4) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/bamf02-c12-526-exchange-20261101`
- [`cb285723a8cd`](https://github.com/Entif-AI/Bilqis-MLX/commit/cb285723a8cdf3f29b061262d4825593553c5180) `docs(bamf): refresh c12 review basis`
- [`b2ce463b1978`](https://github.com/Entif-AI/Bilqis-MLX/commit/b2ce463b19784019a75bb7cc0d906f960023f4ec) `chore(bamf): activate #736 source-positive proof`
- [`066cafd03b54`](https://github.com/Entif-AI/Bilqis-MLX/commit/066cafd03b540e38f17aa57ae42ce1d362de5452) `fix(bamf): defer C07 replay authority to C07`
- [`6a5dc13f37bb`](https://github.com/Entif-AI/Bilqis-MLX/commit/6a5dc13f37bb0c844dd10bf5d2d53be0d74b235d) `fix(bamf): seal issued A02 staging handoffs`
- [`7bae93aad41a`](https://github.com/Entif-AI/Bilqis-MLX/commit/7bae93aad41a3bbfd1fbaec85ddd2f24270798ba) `test(bamf): prove source-positive B06 refinement path`
- [`f749a0a1226e`](https://github.com/Entif-AI/Bilqis-MLX/commit/f749a0a1226e975fb01881c6ca6ad2ecfd9799ff) `chore(bamf): checkpoint #736 source-positive proof`
- [`7bb7567d2a51`](https://github.com/Entif-AI/Bilqis-MLX/commit/7bb7567d2a510ba532f572045f1ed120d13f86c4) `chore(bamf): turn in #736 source-positive proof`
- [`df0c11ea6a68`](https://github.com/Entif-AI/Bilqis-MLX/commit/df0c11ea6a687c062143ebc0b16705f2ca7fee2b) `fix(bamf): bind A02 handoff custody identity`
- [`289331c161c5`](https://github.com/Entif-AI/Bilqis-MLX/commit/289331c161c5dd80132013d28d2532d0213856ef) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/bamf02-a-399-production-admission-20261106`
- [`6b085f875ab7`](https://github.com/Entif-AI/Bilqis-MLX/commit/6b085f875ab781a3771c89916a1e42653f73e882) `feat(bamf): add source-positive B06.3 production witness (#736 / PR #940)`
- [`cba3712f49c3`](https://github.com/Entif-AI/Bilqis-MLX/commit/cba3712f49c346b4d9620f1d012325a3766ae7c5) `chore(bamf): preserve reviewed Lane B state`
- [`d571f16208d8`](https://github.com/Entif-AI/Bilqis-MLX/commit/d571f16208d8504600740b032825021c08e061b4) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/bamf02-a-399-production-admission-20261106`
- [`d9fca0b16ca5`](https://github.com/Entif-AI/Bilqis-MLX/commit/d9fca0b16ca5bb8ef0a877e316d5a53209313959) `docs(bamf): refresh A02 turn-in receipts`
- [`9ae482d45bbf`](https://github.com/Entif-AI/Bilqis-MLX/commit/9ae482d45bbf58636b2a4dea3c2286ba684e67ce) `fix(c12): make acceptance issuance non-transferable`
- [`92549cdf6539`](https://github.com/Entif-AI/Bilqis-MLX/commit/92549cdf6539157916fc4a82e96ecafb333efdd2) `docs(bamf): record c12 issuance repair`
- [`fd8a5cffc051`](https://github.com/Entif-AI/Bilqis-MLX/commit/fd8a5cffc0511a2d0e9f6c9bbab65d07144996de) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/bamf02-c12-526-exchange-20261101`
- [`b45cd6926585`](https://github.com/Entif-AI/Bilqis-MLX/commit/b45cd692658597748ea742151e3c9c5ea50892da) `chore(bamf): refresh c12 proof on current unified`
- [`327dc0de3bfa`](https://github.com/Entif-AI/Bilqis-MLX/commit/327dc0de3bfa5d3a70525edd325747d383e8bd4d) `docs(bamf): freeze c12 current-unified receipt`
- [`1d2564bdb00c`](https://github.com/Entif-AI/Bilqis-MLX/commit/1d2564bdb00cd670dd1fe52bcb33d73f21dc6693) `fix(c12): use canonical factory retention owner`
- [`b60218e821ad`](https://github.com/Entif-AI/Bilqis-MLX/commit/b60218e821adffff10971d524914b4d03f70786c) `docs(bamf): record c12 canonical-owner repair`
- [`e206ec0e957e`](https://github.com/Entif-AI/Bilqis-MLX/commit/e206ec0e957e24823f3136c0f3bffe1fc950013e) `fix(bamf): bind package import to owner-issued authority (C12 / #718 / #526 / PR #941)`
- [`ebf534560d7a`](https://github.com/Entif-AI/Bilqis-MLX/commit/ebf534560d7a3e1d475bd62b1599cbe678dfe381) `chore(bamf): activate #454 reconciliation`
- [`314d63c478f0`](https://github.com/Entif-AI/Bilqis-MLX/commit/314d63c478f0c0393e0c5da8961df708c4dd8c27) `docs(bamf): record #454 reconciliation proof`
- [`a569b19c9f79`](https://github.com/Entif-AI/Bilqis-MLX/commit/a569b19c9f79e1995f857e08a82a539ec971f611) `chore(bamf): turn in #454 reconciliation`
- [`7baf48cfd794`](https://github.com/Entif-AI/Bilqis-MLX/commit/7baf48cfd79436340143b47c6ba01c8ecc3d4702) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/510-c07-atomic-adoption-20261107`
- [`debbe540b24b`](https://github.com/Entif-AI/Bilqis-MLX/commit/debbe540b24bfe06bd6ab79445039f461cc1b0ef) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/bamf02-a-399-production-admission-20261106`
- [`bcc82f86e2c4`](https://github.com/Entif-AI/Bilqis-MLX/commit/bcc82f86e2c409e22329d38c14b757d7e5a0d517) `docs(bamf): reconcile B06.3 production ownership (#454 / PR #942)`
- [`d64df3141671`](https://github.com/Entif-AI/Bilqis-MLX/commit/d64df31416712b51a24c45417b05893c923642cd) `fix(bamf): keep A02 staging cold-import safe`
- [`9b6b81919f2d`](https://github.com/Entif-AI/Bilqis-MLX/commit/9b6b81919f2df356c539ebc6b4810d08bbfeedde) `docs(bamf): refresh A02 current-unified qualification`
- [`474e2f583e74`](https://github.com/Entif-AI/Bilqis-MLX/commit/474e2f583e746d87c3e32eebd04c9c7d477f0671) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/bamf02-a-399-production-admission-20261106`
- [`8bf499f2b3b4`](https://github.com/Entif-AI/Bilqis-MLX/commit/8bf499f2b3b4f3af56328152f2dec4674339352c) `docs(bamf): consume latest unified receipt`
- [`006c6f6cf2d0`](https://github.com/Entif-AI/Bilqis-MLX/commit/006c6f6cf2d09b6c8b66c0682fa135542c58b176) `docs(bamf): record A02 review turn-in`
- [`f8f4bbafaa87`](https://github.com/Entif-AI/Bilqis-MLX/commit/f8f4bbafaa87056bda8665599f81c1c5284dcfd0) `fix(bamf): stage owner-issued vocabulary extension for C07 (A02.1 / PR #943 / #378)`
- [`0fb7708621b8`](https://github.com/Entif-AI/Bilqis-MLX/commit/0fb7708621b8f7d2d3690fe3f80293b6aef91735) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/510-c07-atomic-adoption-20261107`
- [`04f4fc3f6e63`](https://github.com/Entif-AI/Bilqis-MLX/commit/04f4fc3f6e63fb316ebb02004ae57f60973dcebf) `fix(bamf): consume A02 handoff in C07 adoption`
- [`59e57c709881`](https://github.com/Entif-AI/Bilqis-MLX/commit/59e57c7098814d95afce9d38e64f1a55824d7eb9) `docs(bamf): record C07 atomic adoption proof`
- [`cb74d7d280de`](https://github.com/Entif-AI/Bilqis-MLX/commit/cb74d7d280decd9cdd7bd958bdd5153eec2679d4) `docs(bamf): record C07 exact-head review`
- [`6edb0605a013`](https://github.com/Entif-AI/Bilqis-MLX/commit/6edb0605a013bcf83a29524e7e91bc6f0e165714) `docs(bamf): bind C07 review PR`
- [`06c0a29e6706`](https://github.com/Entif-AI/Bilqis-MLX/commit/06c0a29e67066ff621ec319f699472ed4ef48290) `docs(error-control): refresh moved atlas test path`
- [`7927b0fcbe20`](https://github.com/Entif-AI/Bilqis-MLX/commit/7927b0fcbe2007c3b3a3d895d2ac4382c3e73779) `chore(bamf): activate #466 promotion transition`
- [`fb0d4e679954`](https://github.com/Entif-AI/Bilqis-MLX/commit/fb0d4e679954901d485c8a367ed05f034866073a) `test(bamf): factor C07 composed witness helpers`
- [`6a770f10074d`](https://github.com/Entif-AI/Bilqis-MLX/commit/6a770f10074df6f4f8889d439f783ad42f5efe63) `feat(bamf): atomic A02 vocabulary adoption through B13 (BAMF-0.2 C07.1b / PR #944 / #510)`
- [`ab73a5a84bf9`](https://github.com/Entif-AI/Bilqis-MLX/commit/ab73a5a84bf942ac06e76a1bc9849aeb0263e44e) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/466-b09-promotion-transition-20261109`
- [`76b0e074a446`](https://github.com/Entif-AI/Bilqis-MLX/commit/76b0e074a4462dd0475d83c3f834030e36749fb8) `feat(bamf): bind promotion to plasticity transition (#466)`
- [`2cdb42690963`](https://github.com/Entif-AI/Bilqis-MLX/commit/2cdb4269096325a1e188845607b555455726829a) `docs(bamf): checkpoint B09.3 review state (#466)`
- [`5d2f542542fd`](https://github.com/Entif-AI/Bilqis-MLX/commit/5d2f542542fdee2793bdbb4baa73d2c26f4ceba1) `feat(c12): enforce public package export classes`
- [`4f5972b12fe9`](https://github.com/Entif-AI/Bilqis-MLX/commit/4f5972b12fe933ee19701b17ba138a93a5bb7404) `fix(bamf): recheck A02 admission resources`
- [`ef40e18e2a0c`](https://github.com/Entif-AI/Bilqis-MLX/commit/ef40e18e2a0c7688b079142ea1bb09b4d8921024) `fix(bamf): close B09.3 promotion authority gaps (#466)`
- [`c4ce0836a841`](https://github.com/Entif-AI/Bilqis-MLX/commit/c4ce0836a8419b51ccbc5942c76a28c237317ffe) `docs(bamf): refresh B09.3 proof head (#466)`
- [`1acfc1f50f89`](https://github.com/Entif-AI/Bilqis-MLX/commit/1acfc1f50f894e4631307a93a1924a2128efed07) `docs(bamf): checkpoint A02.2 integration proof`
- [`a6e6d3e23ae9`](https://github.com/Entif-AI/Bilqis-MLX/commit/a6e6d3e23ae9e91bc6ac92cdd7aa4d05345ec11f) `fix(bamf): keep B09 transition at owner boundary (#466)`
- [`3d1b0e9c2585`](https://github.com/Entif-AI/Bilqis-MLX/commit/3d1b0e9c258542bbd455aac0a84256d022892b93) `docs(bamf): pin final B09.3 semantic head (#466)`
- [`c1b65c3d1510`](https://github.com/Entif-AI/Bilqis-MLX/commit/c1b65c3d15109746d2033473ceff33c611731b50) `test(bamf): prove B09.3 cold bundle roundtrip (#466)`
- [`097bac8ec34c`](https://github.com/Entif-AI/Bilqis-MLX/commit/097bac8ec34c34382a663c69237c36f2eb6b287d) `docs(bamf): pin B09.3 cold-resume proof (#466)`
- [`0287fc7f4408`](https://github.com/Entif-AI/Bilqis-MLX/commit/0287fc7f4408ce096624f1921079b91c96bf307a) `docs(bamf): record A02.2 detached capacity failure`
- [`066c08028f1f`](https://github.com/Entif-AI/Bilqis-MLX/commit/066c08028f1f8b6c8f7ccc36c285df0ea3c6cfba) `feat(bamf): bind promotion to plasticity transition (#466)`
- [`3aa81f18dba3`](https://github.com/Entif-AI/Bilqis-MLX/commit/3aa81f18dba338b79eff935de96e9d94eda75fae) `fix(c12): bind package export and teacher custody`
- [`4ecb38003576`](https://github.com/Entif-AI/Bilqis-MLX/commit/4ecb38003576ac32e10490c5ee6512710b5a25b5) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/bamf02-c-runtime`
- [`d12acc33f604`](https://github.com/Entif-AI/Bilqis-MLX/commit/d12acc33f604df53936a8456085551c1849d5ae9) `fix(bamf): preserve B09 transition authority on extension (#466)`
- [`09b3b7dfe3b7`](https://github.com/Entif-AI/Bilqis-MLX/commit/09b3b7dfe3b7d5336d29f25b106e925dceff628a) `fix(bamf): defer inactive Atlas bank allocation`
- [`0791af3782e1`](https://github.com/Entif-AI/Bilqis-MLX/commit/0791af3782e1478ecfefbd7ac48f332a59997797) `docs(bamf): record A02.2 genesis capacity repair`
- [`a1e40845c990`](https://github.com/Entif-AI/Bilqis-MLX/commit/a1e40845c990d443a58971eb1c914e9deb244e90) `test(bamf): pin active foundation bank extent`
- [`039fbcab999e`](https://github.com/Entif-AI/Bilqis-MLX/commit/039fbcab999e290dcb3dcd9722924678a460bc4a) `fix(bamf): preserve B09 transition authority on extension (#466)`
- [`e51ed6162880`](https://github.com/Entif-AI/Bilqis-MLX/commit/e51ed616288093129ee5164b74f5f7d119ad55de) `docs(c12): record C12.3 qualification evidence`
- [`64351d421edc`](https://github.com/Entif-AI/Bilqis-MLX/commit/64351d421edcd9594f1f393322fa15936602fc8c) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/bamf02-c-runtime`
- [`9c4a992da594`](https://github.com/Entif-AI/Bilqis-MLX/commit/9c4a992da594f68e06545ad59a0c85c9e5b0ec29) `docs(c12): finalize C12.3 turn-in evidence`
- [`68526365af6b`](https://github.com/Entif-AI/Bilqis-MLX/commit/68526365af6b09686df3634d09d0b7b24de00520) `docs(c12): turn in C12.3 for review`
- [`516725b6170f`](https://github.com/Entif-AI/Bilqis-MLX/commit/516725b6170f258ad86b0c5d4ca050907238e59d) `feat(bamf): validate private-safe exports and local exchange compatibility (PR #946 / #527)`
- [`2e79d882d5b6`](https://github.com/Entif-AI/Bilqis-MLX/commit/2e79d882d5b6a298f2b10187b21563927327e3d6) `test(bamf): prove A02 full adoption recovery`
- [`8b3f071215b2`](https://github.com/Entif-AI/Bilqis-MLX/commit/8b3f071215b27b98f8ae15a9d0b02fc72b7fc80d) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/bamf02-a-semantics`
- [`51125d07cb32`](https://github.com/Entif-AI/Bilqis-MLX/commit/51125d07cb320518bc9ce000719e01375d0e159d) `fix(bamf): make promotion evidence grade-neutral (#948)`
- [`bdd866fa6090`](https://github.com/Entif-AI/Bilqis-MLX/commit/bdd866fa60908783e7d564026c11b37b4164d79e) `test(bamf): satisfy portable hygiene for #948`
- [`d817f6fecafe`](https://github.com/Entif-AI/Bilqis-MLX/commit/d817f6fecafe051cbf7d5beaa6166a528ef961e1) `fix(bamf): preserve release-bound grade neutrality (#948)`
- [`7011f83d74b3`](https://github.com/Entif-AI/Bilqis-MLX/commit/7011f83d74b31c925f2ad9f9695671b5d88d7348) `docs(bamf): record A02.2 post-merge proof`
- [`acf134a74ddb`](https://github.com/Entif-AI/Bilqis-MLX/commit/acf134a74ddbc0446fd69c5e0396cb30c7e59ee8) `docs(bamf): register C16.1c genesis source authority leaf`
- [`8f17a78217b8`](https://github.com/Entif-AI/Bilqis-MLX/commit/8f17a78217b81d4859a2c31bf992bd51d82c60e0) `docs(bamf): record A02.2 exact-head review`
- [`fd8e19a6dc9c`](https://github.com/Entif-AI/Bilqis-MLX/commit/fd8e19a6dc9c4cc7afe0d87619dc4beb1d53403c) `docs(bamf): register C16.1c genesis source-authority prerequisite`
- [`3d3db158c9a0`](https://github.com/Entif-AI/Bilqis-MLX/commit/3d3db158c9a0f69e04477fa89b6825926ad750f0) `docs(bamf): bind A02.2 review PR`
- [`0338f334388a`](https://github.com/Entif-AI/Bilqis-MLX/commit/0338f334388a01389163fb0cba74614c2bcdb83a) `feat(bamf): stage capacity expansion through C07/B13 (BAMF-0.2 A02.2 / #400 / PR #952)`
- [`0840dfb9ab09`](https://github.com/Entif-AI/Bilqis-MLX/commit/0840dfb9ab0941f560e619647c5d858a19c166ac) `feat(bamf): read accepted A02 registry export`
- [`db0bde381ecc`](https://github.com/Entif-AI/Bilqis-MLX/commit/db0bde381eccca4207623014cb1f728258bf4d3e) `fix(bamf): use canonical Atlas bank geometry`
- [`315eee70be1d`](https://github.com/Entif-AI/Bilqis-MLX/commit/315eee70be1dda5c5230d39bf0aad48cb2608f1c) `feat(c16): bind host C09 authority into BAMF genesis`
- [`83fb40d6d242`](https://github.com/Entif-AI/Bilqis-MLX/commit/83fb40d6d242e495a956c160080832e0e2c75a51) `docs(bamf): checkpoint A02.3 accepted export`
- [`781d43f975e7`](https://github.com/Entif-AI/Bilqis-MLX/commit/781d43f975e7030a15ead8d80ca12ecff9676c21) `test(bamf): prove accepted A02 registry export`
- [`476f9005d2ee`](https://github.com/Entif-AI/Bilqis-MLX/commit/476f9005d2ee0d4dc51dc6bbb361b1ba7cb73b8d) `fix(bamf): source-authorize B08 schema reads (#460)`
- [`b23a4ac1be9f`](https://github.com/Entif-AI/Bilqis-MLX/commit/b23a4ac1be9f9616b0765d6b0372bf4a1e50eaa0) `refactor(c16): isolate BAMF genesis preparation`
- [`a6a06ecc25a3`](https://github.com/Entif-AI/Bilqis-MLX/commit/a6a06ecc25a31233ba9f2cce9da411e039f5f36e) `fix(bamf): derive schema family from source owner (#460)`
- [`fb18a4056abf`](https://github.com/Entif-AI/Bilqis-MLX/commit/fb18a4056abf6ee4be2c94c9773275882439e16b) `docs(c16): checkpoint C16.1c authority bridge`
- [`0f442c15ff3d`](https://github.com/Entif-AI/Bilqis-MLX/commit/0f442c15ff3d7b53d99c9fcdb056894055f8b26c) `fix(bamf): route schema errors through control plane (#460)`
- [`919041f5a29e`](https://github.com/Entif-AI/Bilqis-MLX/commit/919041f5a29e9a47ae5b5925ddbddb1c07df194a) `docs(c16): invalidate C16.1c first-writer candidate`
- [`ac5fa6f29530`](https://github.com/Entif-AI/Bilqis-MLX/commit/ac5fa6f295301e5d433d057e6a68eacaa8a4bafe) `docs(c16): propose fixed host C09 genesis authority`
- [`73603ab3d16b`](https://github.com/Entif-AI/Bilqis-MLX/commit/73603ab3d16b3df51e7d1b2d439f282cb74b285b) `fix(c07): bind accepted atlas adoption authority`
- [`ce23bec4d391`](https://github.com/Entif-AI/Bilqis-MLX/commit/ce23bec4d391c1e170b40447bdf6f9163dad428f) `fix(bamf): hold nested motif reads on revoked schema rights (#460)`
- [`0637067e1599`](https://github.com/Entif-AI/Bilqis-MLX/commit/0637067e1599d7679bd64960e58a66c526828ec3) `docs(bamf): close C16.1c host-authority review gaps`
- [`8b03be4881d4`](https://github.com/Entif-AI/Bilqis-MLX/commit/8b03be4881d4450f4f6cba94cfda9b21a2dd2711) `feat(bamf): close A02.3 accepted Registry export boundary (#401)`
- [`c061455ffaff`](https://github.com/Entif-AI/Bilqis-MLX/commit/c061455ffaffb471f7c3d77dd96641ddc4222d41) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/bamf02-c-runtime`
- [`e510ac6ecb73`](https://github.com/Entif-AI/Bilqis-MLX/commit/e510ac6ecb732ce46f9f73bf71352e2d9f66ea01) `docs(bamf): close C16.1c v3 review gaps`
- [`33df8fa9560b`](https://github.com/Entif-AI/Bilqis-MLX/commit/33df8fa9560b2827ad894b923bbc92269a52df99) `docs(bamf): close C16.1c v4 review gaps`
- [`ae310fde0d49`](https://github.com/Entif-AI/Bilqis-MLX/commit/ae310fde0d49f5cea141e58ed4b9ff5f1288d8e9) `docs(bamf): close C16.1c v5 review gap`
- [`14bec894dd55`](https://github.com/Entif-AI/Bilqis-MLX/commit/14bec894dd55b0eb6dc86d5d4fd8462f91e276a4) `test(bamf): prove retained motif B13 custody (#460)`
- [`d613d25d841b`](https://github.com/Entif-AI/Bilqis-MLX/commit/d613d25d841b2ac8da3d75d37ebfc797c3975794) `test(bamf): keep B13 custody witness bounded (#460)`
- [`d3c3d9822cba`](https://github.com/Entif-AI/Bilqis-MLX/commit/d3c3d9822cbaad0c5388d863c64afe686ac9c8bc) `docs(bamf): close C16.1c v6 readiness gap`
- [`b685f5939601`](https://github.com/Entif-AI/Bilqis-MLX/commit/b685f5939601a47be0f55195e25a2a9c7421a765) `docs(bamf): reconcile live flow control for 509`
- [`f50c42c48188`](https://github.com/Entif-AI/Bilqis-MLX/commit/f50c42c481885b1506a708d086c62e80913f1beb) `docs(bamf): preserve merged PR history`
- [`40fae87c2d42`](https://github.com/Entif-AI/Bilqis-MLX/commit/40fae87c2d426aaa8476b197ba1fe0cb926b9010) `docs(bamf): close C16.1c v7 review packet`
- [`8212c6aa3b13`](https://github.com/Entif-AI/Bilqis-MLX/commit/8212c6aa3b13a335fa1ce93be78d184555b3398a) `fix(bamf): cold resume after atlas adoption`
- [`8cf12059bcfe`](https://github.com/Entif-AI/Bilqis-MLX/commit/8cf12059bcfeec2fd9859b8d9053c56abc63e363) `docs(bamf): checkpoint 509 cold resume bridge`
- [`39d75ce0593f`](https://github.com/Entif-AI/Bilqis-MLX/commit/39d75ce0593f7a8cf74a4c152f83089a8a9a05bc) `fix(bamf): preserve A13 schema-right authority (#956)`
- [`4696b33732ee`](https://github.com/Entif-AI/Bilqis-MLX/commit/4696b33732ee7a4d514db2476896943b08382312) `docs(bamf): reconcile live flow control for 509`
- [`549473724f6b`](https://github.com/Entif-AI/Bilqis-MLX/commit/549473724f6b0a15c33ff9a315f3b1c1ab784e17) `docs(bamf): preserve merged PR history`
- [`1a50cfec0323`](https://github.com/Entif-AI/Bilqis-MLX/commit/1a50cfec0323dd6a5e46938e27f53a9aadc34e46) `docs(bamf): activate atlas source locator remediation`
- [`236cfad999e7`](https://github.com/Entif-AI/Bilqis-MLX/commit/236cfad999e7f6ea24dd90281af639ed161f807b) `fix(bamf): resolve atlas source bundles by content id`
- [`4ac234c80f9d`](https://github.com/Entif-AI/Bilqis-MLX/commit/4ac234c80f9dbae2c1b40cdff4d8aba4aeea74af) `test(bamf): harden atlas source locator roots`
- [`efbde03820d8`](https://github.com/Entif-AI/Bilqis-MLX/commit/efbde03820d8b6a0924d90f8897ba201d2349c77) `fix(bamf): enforce schema-right owner lineage (#956)`
- [`a74d30dce672`](https://github.com/Entif-AI/Bilqis-MLX/commit/a74d30dce672c2597fef027211d19131526bbbfa) `docs(bamf): checkpoint 959 source locator`
- [`df54499a4627`](https://github.com/Entif-AI/Bilqis-MLX/commit/df54499a4627dea9e14836026ce7dfb3431411a2) `docs(bamf): reconcile live flow control for 509`
- [`31972e1e04cb`](https://github.com/Entif-AI/Bilqis-MLX/commit/31972e1e04cb9033686e7003f1408ca785bda115) `docs(bamf): preserve merged PR history`
- [`995b115b4974`](https://github.com/Entif-AI/Bilqis-MLX/commit/995b115b49741f73071c74000af008d9289d95d8) `docs(bamf): activate atlas source locator remediation`
- [`e3e629b314b1`](https://github.com/Entif-AI/Bilqis-MLX/commit/e3e629b314b17f766f7ac1d6184d60f84a6721a8) `docs(bamf): activate A09 C07 scope remediation`
- [`09c9b50ac29b`](https://github.com/Entif-AI/Bilqis-MLX/commit/09c9b50ac29b2ab14e18175f828332427513ed2a) `test(bamf): bind retained custody to executing generation (#460)`
- [`3495b6572e01`](https://github.com/Entif-AI/Bilqis-MLX/commit/3495b6572e0189777872009bffde6bde0456de78) `fix(bamf): bind A09 delta scope for C07`
- [`349da6d3dcb6`](https://github.com/Entif-AI/Bilqis-MLX/commit/349da6d3dcb67e9b710d080c82ba410ff84aca50) `fix(bamf): seal source-owned schema grant scope (#956)`
- [`05d7d5fdd3ec`](https://github.com/Entif-AI/Bilqis-MLX/commit/05d7d5fdd3ec96141068ddccb0e81fe7a08733d4) `fix(bamf): preserve A13 schema-right continuity (#956)`
- [`666ba61a40e1`](https://github.com/Entif-AI/Bilqis-MLX/commit/666ba61a40e1d77031cce3c448b616e07b7fc813) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/460-b08-qualified-motif-20261109`
- [`6ddd5fca6275`](https://github.com/Entif-AI/Bilqis-MLX/commit/6ddd5fca627583f9dd6925cc7f265d09665fcac0) `docs(bamf): close C16.1c v8 review gaps`
- [`bde134d4d06c`](https://github.com/Entif-AI/Bilqis-MLX/commit/bde134d4d06c22077c4d3dd961c4ffa74a9f7807) `fix(bamf): consume source-owned schema rights (#460)`
- [`96ee4de00a7b`](https://github.com/Entif-AI/Bilqis-MLX/commit/96ee4de00a7b6e5b79985b457eb5361e88b0a8fe) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/948-b09-grade-neutral-evidence-20261109`
- [`f3832960e2af`](https://github.com/Entif-AI/Bilqis-MLX/commit/f3832960e2af6ae07f696efd1effb909166b1341) `docs(bamf): separate C16.1c retry caller contracts`
- [`4344f2238f04`](https://github.com/Entif-AI/Bilqis-MLX/commit/4344f2238f044ab298ff71048cb95981c2e88213) `docs(bamf): record C16.1c v10 EGM pass`
- [`6868e129b513`](https://github.com/Entif-AI/Bilqis-MLX/commit/6868e129b51343fb3a3fab366c93d2ba5485c396) `test(bamf): target owner-issued schema grant (#460)`
- [`7a6c048e9325`](https://github.com/Entif-AI/Bilqis-MLX/commit/7a6c048e9325a877b9b3451c731be3545a11ee69) `Merge pull request #949 from Entif-AI/codex/948-b09-grade-neutral-evidence-20261109`
- [`000e53e174ee`](https://github.com/Entif-AI/Bilqis-MLX/commit/000e53e174eea703a9adb0aabcca2b5ec1707af8) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/959-atlas-source-locator-20261109`
- [`b9ce1e73fbc1`](https://github.com/Entif-AI/Bilqis-MLX/commit/b9ce1e73fbc196532642635ba5f08d73d2eca885) `docs(bamf): reconcile 959 flow control after unified sync`
- [`59aacc36a802`](https://github.com/Entif-AI/Bilqis-MLX/commit/59aacc36a80248cb2c698b8a343b31f961441b12) `feat(bamf): add fixed C09 host authority boundary`
- [`b894a1f100a1`](https://github.com/Entif-AI/Bilqis-MLX/commit/b894a1f100a1cd623dbc9127cf11e9d17bb69f19) `feat(bamf): report motif read participation (#461)`
- [`bc5c524ec382`](https://github.com/Entif-AI/Bilqis-MLX/commit/bc5c524ec3828b67661b44e8e576338ee7e46068) `fix(bamf): reject wrong Atlas source id before staging`
- [`e32b9b305e23`](https://github.com/Entif-AI/Bilqis-MLX/commit/e32b9b305e236488d7a7da4fac1ffa8eae964721) `docs(bamf): record 959 source-id ordering repair`
- [`9a35db7293e0`](https://github.com/Entif-AI/Bilqis-MLX/commit/9a35db7293e02be687aed9c07a8c5ab0df0ebed9) `docs(bamf): mark 959 ready for human review`
- [`eaa73be82cf1`](https://github.com/Entif-AI/Bilqis-MLX/commit/eaa73be82cf1adac32786d4242868b8e360af5d2) `fix(bamf): source-authorize B08 schema reads (#460)`
- [`19757bb67388`](https://github.com/Entif-AI/Bilqis-MLX/commit/19757bb67388c8cbcd72d63d2d4b343aef8c53e1) `fix(bamf): scope 959 ready transition to its lane row`
- [`dbd78411021b`](https://github.com/Entif-AI/Bilqis-MLX/commit/dbd78411021b70179eb4e831770fa968b59d1ae5) `Merge latest reviewed BAMF unified into #959`
- [`d12e5ecf6669`](https://github.com/Entif-AI/Bilqis-MLX/commit/d12e5ecf6669aeefb18f1d9098d31b4ad1040471) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/bamf02-b-neural`
- [`bbfe58d99791`](https://github.com/Entif-AI/Bilqis-MLX/commit/bbfe58d997918507f20f1d6f5225e3643ba73d03) `feat(bamf): bind C09 authority through generation custody`
- [`53cb90576e8e`](https://github.com/Entif-AI/Bilqis-MLX/commit/53cb90576e8e939776ff0ba712b16064196bf0dc) `docs(bamf): freeze synchronized 959 closeout proof`
- [`f0c4dd86676f`](https://github.com/Entif-AI/Bilqis-MLX/commit/f0c4dd86676f7b1515e925c0d08ae5d1714f2de6) `feat(bamf): cut C09 consumers to accepted custody`
- [`872f8dfff152`](https://github.com/Entif-AI/Bilqis-MLX/commit/872f8dfff152cfc3bb7f7df8aaf2c178da629862) `fix(bamf): resolve Atlas source bundles by content identity (#959)`
- [`c8890f64f354`](https://github.com/Entif-AI/Bilqis-MLX/commit/c8890f64f35467d9df3750a484231e0788492bb1) `docs(bamf): close C16.1c implementation proof`
- [`331db08d7c89`](https://github.com/Entif-AI/Bilqis-MLX/commit/331db08d7c89824f7f6d78562ee75c807f0456f3) `feat(bamf): persist motif participation and place mid-depth read (#461 / BAMF-0.2 B08.2 / PR #962)`
- [`1b6c3b26123f`](https://github.com/Entif-AI/Bilqis-MLX/commit/1b6c3b26123fc797a92ed131a71c0dc826913fc5) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/958-a09-c07-scope-20261109`
- [`b6c607963738`](https://github.com/Entif-AI/Bilqis-MLX/commit/b6c607963738b7e9504324f64b0e17ac0c978ca4) `test(bamf): close C16.1c drift proof gaps`
- [`32371aa167f3`](https://github.com/Entif-AI/Bilqis-MLX/commit/32371aa167f38f82da04496af4d0fd5525ae40d5) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/bamf02-c-runtime`
- [`d23004a02eb7`](https://github.com/Entif-AI/Bilqis-MLX/commit/d23004a02eb766965688ab5d998a4af1fe092968) `fix(bamf): type atlas admission contract failure`
- [`d3d032d0a802`](https://github.com/Entif-AI/Bilqis-MLX/commit/d3d032d0a802b7acf9391e12b4bf7b6ca70b5c24) `fix(bamf): align Darwin host authority contract`
- [`de3cd73a3f91`](https://github.com/Entif-AI/Bilqis-MLX/commit/de3cd73a3f91f7230b294f8d4f74ce4a5ea627e5) `fix(bamf): harden A09 C07 scope handoff`
- [`b37456410350`](https://github.com/Entif-AI/Bilqis-MLX/commit/b374564103501802a2d4c69d77510ce207679226) `test(bamf): prove fail-closed operator disposition`
- [`c698512d15d0`](https://github.com/Entif-AI/Bilqis-MLX/commit/c698512d15d0f0494f7a6f702d274d9c2a9183a0) `docs(bamf): reconcile C16.1c drift evidence`
- [`0cf011b18c3e`](https://github.com/Entif-AI/Bilqis-MLX/commit/0cf011b18c3e5429732e4c654c78f2d8702dda3c) `fix(bamf): centralize world operator authority`
- [`e259d1317658`](https://github.com/Entif-AI/Bilqis-MLX/commit/e259d13176580348679ee5d7703b0ad0d4174d2f) `fix(bamf): bind JIT profile authority`
- [`2f83ecc9601d`](https://github.com/Entif-AI/Bilqis-MLX/commit/2f83ecc9601d326366a3be857eaeaed2031effa9) `fix(bamf): bind A09 receipt frontier`
- [`3b4e1566680d`](https://github.com/Entif-AI/Bilqis-MLX/commit/3b4e1566680d99ffe7bfb59b3ad1b7d83e155d07) `feat(bamf): bind accepted Atlas adoption authority (BAMF-0.2 C07.1a / PR #954 / #509)`
- [`6e3d9bb29ae1`](https://github.com/Entif-AI/Bilqis-MLX/commit/6e3d9bb29ae10fed573a921fc12015380416e5d9) `Merge branch 'codex/bamf-unified-base-20261028' into codex/950-c09-genesis-source-authority-20261109`
- [`2c572202978d`](https://github.com/Entif-AI/Bilqis-MLX/commit/2c572202978df9542e379cfb975007cdea3f05ad) `feat(bamf): bind host-owned C09 authority into generation-zero custody (BAMF-0.2 C16.1c / PR #963 / #950)`
- [`e7de7b167b26`](https://github.com/Entif-AI/Bilqis-MLX/commit/e7de7b167b269365862ec968819539ef32a0ad0b) `docs(bamf): activate C16.1a after C16.1c merge`
- [`f85ada748d19`](https://github.com/Entif-AI/Bilqis-MLX/commit/f85ada748d19179db4874369cae22726d843fa65) `fix(c11): complete BAMF create and resume lifecycle`
- [`494cebb3631d`](https://github.com/Entif-AI/Bilqis-MLX/commit/494cebb3631d99d8823975f74f5bc653033aed92) `fix(c11): harden BAMF create resume authority`
- [`82c50e8f31af`](https://github.com/Entif-AI/Bilqis-MLX/commit/82c50e8f31af9d6cb93e3c9ad38f580b084b01e7) `fix(c11): preserve staged genesis authority boundary`
- [`38b91e887f92`](https://github.com/Entif-AI/Bilqis-MLX/commit/38b91e887f929f8cab1b957355fc1d9ac8c6d908) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/958-a09-c07-scope-20261109`
- [`291f7a39cc6f`](https://github.com/Entif-AI/Bilqis-MLX/commit/291f7a39cc6f083c222fff604e8a3d95ab98e497) `feat(bamf): persist C07 policy on first-student create`
- [`3078d363f142`](https://github.com/Entif-AI/Bilqis-MLX/commit/3078d363f142c87f8cf84fe0d0e96473d364c205) `fix(bamf): bind v2 atlas admission authority`
- [`50c8c8bf6a51`](https://github.com/Entif-AI/Bilqis-MLX/commit/50c8c8bf6a511877e9291b62e20e2b074b7e8ed1) `fix(bamf): wire v2 atlas admission owners`
- [`355663100332`](https://github.com/Entif-AI/Bilqis-MLX/commit/355663100332cdc0aba7530804af657fd0f0169e) `refactor(bamf): isolate v2 atlas admission facts`
- [`249380dc678c`](https://github.com/Entif-AI/Bilqis-MLX/commit/249380dc678cbac768c7ced021e62644d67eeba6) `test(bamf): harden v2 atlas authority replay`
- [`831c393f80e4`](https://github.com/Entif-AI/Bilqis-MLX/commit/831c393f80e42366be5e66a44febb4cc78374b6e) `test(bamf): rebind B08 custody proof to host authority (#964)`
- [`5677d4df08b6`](https://github.com/Entif-AI/Bilqis-MLX/commit/5677d4df08b604b86cdc45d39e7b2e59882107ac) `fix(bamf): preserve v1 atlas import order`
- [`6e73e21f8d53`](https://github.com/Entif-AI/Bilqis-MLX/commit/6e73e21f8d5312adf17b524758f6169adfca4873) `docs(bamf): checkpoint 958 review gate`
- [`9903de1b2977`](https://github.com/Entif-AI/Bilqis-MLX/commit/9903de1b2977202f3c46548feec00bc6f1135456) `docs(bamf): explain 958 review hold`
- [`7e114d930b78`](https://github.com/Entif-AI/Bilqis-MLX/commit/7e114d930b7841fce83e45c9a8630637af9dc948) `docs(bamf): defer distributed leaves to 0.3 (#966)`
- [`bd8c70c75e86`](https://github.com/Entif-AI/Bilqis-MLX/commit/bd8c70c75e86d008fc23c2a7bfa66843bbeb2037) `docs(bamf): design C16.1a accepted enrollment retry`
- [`61486479e256`](https://github.com/Entif-AI/Bilqis-MLX/commit/61486479e256f1af3db75dcf9a82d1d1629029a1) `docs(bamf): clean C16.1a proposal receipt`
- [`d97ce94dd00a`](https://github.com/Entif-AI/Bilqis-MLX/commit/d97ce94dd00aeee04c36a77e67193b5a5b0471d1) `docs(bamf): freeze C16.1a for enrollment design review`
- [`aa0555b7c3df`](https://github.com/Entif-AI/Bilqis-MLX/commit/aa0555b7c3df753d901c3cee57c86623a420067f) `fix(bamf): reject superseded atlas v2 lease`
- [`bc0b905ebb2e`](https://github.com/Entif-AI/Bilqis-MLX/commit/bc0b905ebb2ed970e05f73c4210f792d42ec9441) `fix(bamf): rebind retained-custody proof to host-owned C09 trust root (BAMF-0.2 B08.3 / PR #968 / #964)`
- [`cc8f0d38d67a`](https://github.com/Entif-AI/Bilqis-MLX/commit/cc8f0d38d67a3b1d353280c20a7f3e450c6e07a8) `docs(bamf): defer distributed leaves to BAMF v0.3`
- [`b170748da19d`](https://github.com/Entif-AI/Bilqis-MLX/commit/b170748da19d3586fe9609b5547ff768bc1cb814) `docs(bamf): turn in 958 after clean review`
- [`1a1bcbf3c58b`](https://github.com/Entif-AI/Bilqis-MLX/commit/1a1bcbf3c58b0d851e40dbdee847c3fb3c00ec3a) `feat(bamf): bind A09 staged scope to C07 v2 admission authority (BAMF-0.2 #958 / PR #967)`
- [`4f59da2cb6bf`](https://github.com/Entif-AI/Bilqis-MLX/commit/4f59da2cb6bf1ec6a226fa6b7a3ef6a3f3df876e) `feat(bamf): bind generation-active semantic rows (#439 #970)`
- [`2fdce5149286`](https://github.com/Entif-AI/Bilqis-MLX/commit/2fdce514928672c5491513cb4c446aea97f902aa) `docs(bamf): repair C16.1a enrollment contract`
- [`b357ab77c91b`](https://github.com/Entif-AI/Bilqis-MLX/commit/b357ab77c91b83d85fcb3ba5e45712e30bbd75e3) `docs(bamf): record C16.1a design EGM repair`
- [`7a515a01ec40`](https://github.com/Entif-AI/Bilqis-MLX/commit/7a515a01ec407ed0942e48711aaaeb0ec2dadd2f) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/bamf02-c-runtime`
- [`791ef1de7429`](https://github.com/Entif-AI/Bilqis-MLX/commit/791ef1de74291a271788de8d9b652f53523d1b59) `docs(bamf): rebase C16.1a contract on C07 v2`
- [`bbc27aa49479`](https://github.com/Entif-AI/Bilqis-MLX/commit/bbc27aa4947976e66073c9dd3c903fff2af8cf8e) `docs(bamf): checkpoint C16.1a v2 review gate`
- [`5248d5bfcf03`](https://github.com/Entif-AI/Bilqis-MLX/commit/5248d5bfcf03655144013e225ba5d8dae64ac1ba) `feat(bamf): wire retained motif input read`
- [`10069893edfc`](https://github.com/Entif-AI/Bilqis-MLX/commit/10069893edfc57de6b1d0fd1e2800102c9e6016e) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/965-b08-input-motif-read-20261110`
- [`a541b49b143a`](https://github.com/Entif-AI/Bilqis-MLX/commit/a541b49b143a6c2ddfab46ce0444e597b145c2f2) `refactor(bamf): split retained receipt replay`
- [`0d8fc9660f7c`](https://github.com/Entif-AI/Bilqis-MLX/commit/0d8fc9660f7cb5c3eb1f1359b11c8d0d370b4989) `refactor(bamf): split B02 authority ownership modules (#439 #970)`
- [`d98beee7314a`](https://github.com/Entif-AI/Bilqis-MLX/commit/d98beee7314a88c8c9ae9f1a16d8db47814899f9) `docs(bamf): repair C16.1a second EGM findings`
- [`585709f85702`](https://github.com/Entif-AI/Bilqis-MLX/commit/585709f8570219eecc73a9c80540670ab07e7d0a) `docs(bamf): checkpoint C16.1a R3 review gate`
- [`c501d5053f64`](https://github.com/Entif-AI/Bilqis-MLX/commit/c501d5053f64b1cbb29bd2fc8fc9549137dddce2) `feat(bamf): wire retained motif input read (BAMF-0.2 B08.4 / PR #972 / #965 / #366)`
- [`57652f40973b`](https://github.com/Entif-AI/Bilqis-MLX/commit/57652f40973bbf099947a94229f73856aaccdfa4) `refactor(bamf): compartmentalize model execution tests (#439 #970)`
- [`7270a0ab7cee`](https://github.com/Entif-AI/Bilqis-MLX/commit/7270a0ab7ceeb6427e24b96ef15bb483b3eb47e6) `docs(bamf): restore 0.2 launch and release boundaries`
- [`77abb5747a42`](https://github.com/Entif-AI/Bilqis-MLX/commit/77abb5747a4248b67a13e4e17e076fc5e49f876c) `docs(bamf): freeze #439 structural qualification (#970)`
- [`7e86bfeb46d1`](https://github.com/Entif-AI/Bilqis-MLX/commit/7e86bfeb46d129dbf82b50c1fc200be7623958fc) `docs(bamf): repair C16.1a R3 findings`
- [`3b1c708b2cb8`](https://github.com/Entif-AI/Bilqis-MLX/commit/3b1c708b2cb830c5691d5f3ac8dcf6ba5c5bb358) `docs(bamf): checkpoint C16.1a R4 review gate`
- [`9f0ce8e00422`](https://github.com/Entif-AI/Bilqis-MLX/commit/9f0ce8e0042277b2723ccb3a03f1019e80c200e8) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/bamf02-c-runtime`
- [`78adf3990d3a`](https://github.com/Entif-AI/Bilqis-MLX/commit/78adf3990d3a3aa28af3981eb18688840e06655f) `docs(bamf): rebase C16.1a R4 on current unified`
- [`8027c36e42ab`](https://github.com/Entif-AI/Bilqis-MLX/commit/8027c36e42ab3065e5de4196442065bbd908bc13) `docs(bamf): checkpoint current-unified C16.1a R4 gate`
- [`905018b0ece7`](https://github.com/Entif-AI/Bilqis-MLX/commit/905018b0ece7613843570dc2c2e72a74dae4e91d) `docs(bamf): restore launch and release boundaries`
- [`bcfa7566f9b2`](https://github.com/Entif-AI/Bilqis-MLX/commit/bcfa7566f9b250648badb920aa3c45f7d426ca93) `fix(bamf): preserve extracted public contract identity (#439 #970)`
- [`3abe93ad85b7`](https://github.com/Entif-AI/Bilqis-MLX/commit/3abe93ad85b78684c69e9c737f9389090c25da4e) `merge(bamf): consume reviewed unified for #439 closeout`
- [`3772cf7d29f7`](https://github.com/Entif-AI/Bilqis-MLX/commit/3772cf7d29f76b2daff0fd6e89216e74fba371fb) `test(bamf): pin factory release adoption custody`
- [`c76f0b05f6e6`](https://github.com/Entif-AI/Bilqis-MLX/commit/c76f0b05f6e60846c62a386cf9203869098bd673) `feat(bamf): define factory release adoption custody`
- [`88ae61d50282`](https://github.com/Entif-AI/Bilqis-MLX/commit/88ae61d502820d7c50e3145d36fe492b4865c3ed) `docs(bamf): refresh #439 proof on current unified`
- [`a3c5e379119b`](https://github.com/Entif-AI/Bilqis-MLX/commit/a3c5e379119b2cb5ba2032caa6ec455abcc83bbc) `docs(bamf): repair C16.1a R4 review findings`
- [`09d9ea0474fd`](https://github.com/Entif-AI/Bilqis-MLX/commit/09d9ea0474fd28fda14588415b338590eb67d47c) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/bamf02-c-runtime`
- [`0d9b9303fb48`](https://github.com/Entif-AI/Bilqis-MLX/commit/0d9b9303fb481804124839a6a723a4071a511251) `docs(bamf): rebase C16.1a R5 on current unified`
- [`1a6211b4c1c3`](https://github.com/Entif-AI/Bilqis-MLX/commit/1a6211b4c1c320e8a1c7e266d5ae5d0bd6bfa21e) `docs(bamf): checkpoint C16.1a R5 review gate`
- [`703b913c2dc6`](https://github.com/Entif-AI/Bilqis-MLX/commit/703b913c2dc6ff7e86b38f62e55dc9712f33563c) `docs(bamf): pin C16.1a R5 owner base`
- [`ab2fc2d8837d`](https://github.com/Entif-AI/Bilqis-MLX/commit/ab2fc2d8837d7ae3c7b89f993fbd90d874456026) `docs(bamf): checkpoint pinned C16.1a R5`
- [`3d46999e1fe0`](https://github.com/Entif-AI/Bilqis-MLX/commit/3d46999e1fe0954e2e40684b94eba18a0a9febed) `test(bamf): align retained fixtures with generation custody (#439 #970)`
- [`94e30baaa875`](https://github.com/Entif-AI/Bilqis-MLX/commit/94e30baaa87590f44fe6a8881809deab9d27eef7) `test(bamf): close B08 parent discriminator`
- [`1175bd750817`](https://github.com/Entif-AI/Bilqis-MLX/commit/1175bd750817783bb9d48d7dfc2fd4c32dfd514b) `test(bamf): thread banks through retained backbone witness (#439)`
- [`a7bc0d1cb657`](https://github.com/Entif-AI/Bilqis-MLX/commit/a7bc0d1cb657e5480040ffa0ad03565902fd8388) `test(bamf): harden B08 final proof`
- [`e2f6de923868`](https://github.com/Entif-AI/Bilqis-MLX/commit/e2f6de9238680f58d4755b220b591521e34929de) `refactor(bamf): finish model test directory split`
- [`78da04bbd9cc`](https://github.com/Entif-AI/Bilqis-MLX/commit/78da04bbd9cc9f36678de1c9a12b66273cd9fa9e) `feat(bamf): implement C16.1a create dry-run resume`
- [`3e547b1983a5`](https://github.com/Entif-AI/Bilqis-MLX/commit/3e547b1983a5065309b53693c8fb4fb34e7328de) `docs(bamf): align C16.1a operator contract with R5`
- [`7ccee17c6e6b`](https://github.com/Entif-AI/Bilqis-MLX/commit/7ccee17c6e6b5af15c36e647fc095d429bc56a71) `docs(bamf): qualify #439 final evidence (#439 #970)`
- [`de0bfa0355b2`](https://github.com/Entif-AI/Bilqis-MLX/commit/de0bfa0355b2960088f95a12d9a94a39bf6662a9) `docs(bamf): repair C16.1a R5 review findings`
- [`d4cfd58b1386`](https://github.com/Entif-AI/Bilqis-MLX/commit/d4cfd58b1386a8df64d3d19caae65518c01ab1e8) `docs(bamf): checkpoint C16.1a R6 review gate`
- [`8c616abce9da`](https://github.com/Entif-AI/Bilqis-MLX/commit/8c616abce9da33674cb5958ee4ae4b2c21f5e558) `docs(bamf): repair C16.1a R6 review findings`
- [`3d1fa87e9341`](https://github.com/Entif-AI/Bilqis-MLX/commit/3d1fa87e9341a5be73ae661be850c1073a1ab736) `docs(bamf): checkpoint C16.1a R7 review gate`
- [`77e787df7846`](https://github.com/Entif-AI/Bilqis-MLX/commit/77e787df7846e16767c2fa20f776f22c0e340aab) `fix(bamf): keep feature custody portable (#439 #970)`
- [`3848ab306341`](https://github.com/Entif-AI/Bilqis-MLX/commit/3848ab306341987d30744cc88d4f7c849497dfc0) `docs(bamf): turn in #439 and #970 (#439 #970)`
- [`c8b655a1dfc9`](https://github.com/Entif-AI/Bilqis-MLX/commit/c8b655a1dfc910fae6edd038d7795fed7e5d6407) `docs(bamf): repair C16.1a R7 review findings`
- [`aaf503341bb7`](https://github.com/Entif-AI/Bilqis-MLX/commit/aaf503341bb76965a697bece5b5b60a981e3f52a) `docs(bamf): checkpoint C16.1a R8 review gate`
- [`7908ac1e80f7`](https://github.com/Entif-AI/Bilqis-MLX/commit/7908ac1e80f711b3dca44ea6dc3c2ff6c1ae2581) `docs(bamf): repair C16.1a R8 review findings`
- [`440f4a85f3d2`](https://github.com/Entif-AI/Bilqis-MLX/commit/440f4a85f3d20ac4278519f6cb0b3c4c369ffcf5) `docs(bamf): checkpoint C16.1a R9 review gate`
- [`1219ce788b6c`](https://github.com/Entif-AI/Bilqis-MLX/commit/1219ce788b6cf932d264f84b8b5ef4c0c62b80ab) `test(bamf): tighten B08 proof scope`
- [`937dcfc82cfb`](https://github.com/Entif-AI/Bilqis-MLX/commit/937dcfc82cfbc03fcb8220fd318a20019bfa005e) `feat(bamf): requalify generation-active semantic rows (BAMF-0.2 B02.1 / #439 / #970 / PR #976)`
- [`4fa3ce4a25d5`](https://github.com/Entif-AI/Bilqis-MLX/commit/4fa3ce4a25d5f3d895c664168a72e11e4f00f5c4) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/974-b08-parent-proof-20261110`
- [`ae06ae835c99`](https://github.com/Entif-AI/Bilqis-MLX/commit/ae06ae835c996d15b958bffc85e87eddd67069c3) `refactor(bamf): split retained model fixture support`
- [`7241e325b320`](https://github.com/Entif-AI/Bilqis-MLX/commit/7241e325b320c4a8035fa19bb371e939c9e7d669) `test(bamf): normalize retained support formatting`
- [`2f5f0ce14ee2`](https://github.com/Entif-AI/Bilqis-MLX/commit/2f5f0ce14ee2ba89017c0c2343136dbe3e2eb0c1) `feat(bamf): requalify B02.2 staged initialization (#440)`
- [`5aa2ba9c7ed5`](https://github.com/Entif-AI/Bilqis-MLX/commit/5aa2ba9c7ed5e4845fda8272a3e7099fe8ffa991) `fix(bamf): replay A02 allocation plan (#440)`
- [`bee887dafa04`](https://github.com/Entif-AI/Bilqis-MLX/commit/bee887dafa04db1a9ae7e05585c8cacd5a447d31) `test(bamf): bind retained proof to active semantic rows`
- [`e0abdb5f537d`](https://github.com/Entif-AI/Bilqis-MLX/commit/e0abdb5f537df680c32ba56ab341f8240d41ffba) `fix(bamf): pin A02 source replay authority (#440)`
- [`f55997297728`](https://github.com/Entif-AI/Bilqis-MLX/commit/f559972977289577b2ba8bcc04cd84822da90152) `docs(bamf): turn in B02.2 #440 (#440)`
- [`9ba805c8c484`](https://github.com/Entif-AI/Bilqis-MLX/commit/9ba805c8c48407e287e642f26dc1ae4efb037324) `refactor(bamf): split create and resume operator tests`
- [`5689e0fdfa0f`](https://github.com/Entif-AI/Bilqis-MLX/commit/5689e0fdfa0f219c818ea1039d1070e3b9152647) `docs(bamf): repair C16.1a R9 review findings`
- [`411f452feff5`](https://github.com/Entif-AI/Bilqis-MLX/commit/411f452feff5b81fbb14066101674d2bc851346c) `docs(bamf): checkpoint C16.1a R10 review gate`
- [`e8d28a9ed6bc`](https://github.com/Entif-AI/Bilqis-MLX/commit/e8d28a9ed6bc46282eca702ad4c69a23964d1cf8) `feat(bamf): requalify staged identity initialization (#440 / BAMF-0.2 B02.2 / PR #977)`
- [`8e934ad128a4`](https://github.com/Entif-AI/Bilqis-MLX/commit/8e934ad128a4097d771eeb4f8ffbf35414390468) `docs(bamf): repair C16.1a R10 review findings`
- [`a7d64b6e5d4a`](https://github.com/Entif-AI/Bilqis-MLX/commit/a7d64b6e5d4a29fedaf9ad91b6fc1b4113287412) `docs(bamf): checkpoint C16.1a R11 review gate`
- [`29cf28277c0c`](https://github.com/Entif-AI/Bilqis-MLX/commit/29cf28277c0cd622b26dcfb85d5117bf9ee3df37) `test(bamf): requalify B02.3 registry coverage (#441)`
- [`be97113b5711`](https://github.com/Entif-AI/Bilqis-MLX/commit/be97113b5711fbf138a99f6bb1879b02a91aded9) `test(bamf): tighten B02.3 constructor ledger proof (#441)`
- [`d1f57d845e4b`](https://github.com/Entif-AI/Bilqis-MLX/commit/d1f57d845e4b9b42c31d4ce84bf0c1ccd91bd727) `docs(bamf): turn in B02.3 #441 (#441)`
- [`97c9e15f8ecb`](https://github.com/Entif-AI/Bilqis-MLX/commit/97c9e15f8ecb94315cd1066581de854496bccb8d) `docs(bamf): repair C16.1a R11 review findings`
- [`c21c57e5203a`](https://github.com/Entif-AI/Bilqis-MLX/commit/c21c57e5203a20e2adbf1c0a24a3b4a0f7519a2a) `docs(bamf): checkpoint C16.1a R12 review gate`
- [`555171ae3d4a`](https://github.com/Entif-AI/Bilqis-MLX/commit/555171ae3d4ac3132221dac59a893f5c08ccdbbf) `feat(bamf): requalify shared tensor registry coverage (#441 / BAMF-0.2 B02.3 / PR #978)`
- [`44244f8c55af`](https://github.com/Entif-AI/Bilqis-MLX/commit/44244f8c55af26034dec90cafc757005f1b462bf) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/974-b08-parent-proof-20261110`
- [`a8121769e0c0`](https://github.com/Entif-AI/Bilqis-MLX/commit/a8121769e0c07ca7ec8c5cbd8fb704a5fa613ab5) `test(bamf): witness B02 same-ID role sensitivity (#979)`
- [`9bb7ead6fbd9`](https://github.com/Entif-AI/Bilqis-MLX/commit/9bb7ead6fbd9ef7e703cb397276e31cd42e452f3) `docs(bamf): repair C16.1a R12 review findings`
- [`22a27b59443b`](https://github.com/Entif-AI/Bilqis-MLX/commit/22a27b59443bc9cb86c7286f398fca1c25ebf500) `docs(bamf): checkpoint C16.1a R13 review gate`
- [`8e1b34bb84aa`](https://github.com/Entif-AI/Bilqis-MLX/commit/8e1b34bb84aa95e08918daa0d4cd74322a0099e5) `docs(bamf): turn in B02 parent mitigation #979 (#979)`
- [`7c50c69ff1e1`](https://github.com/Entif-AI/Bilqis-MLX/commit/7c50c69ff1e1f66d7794ee71e192f110d25f1ccb) `fix(bamf): direct same-ID role-sensitivity witness (#979 / BAMF-0.2 B02 mitigation / PR #980)`
- [`7f99502ea09c`](https://github.com/Entif-AI/Bilqis-MLX/commit/7f99502ea09cdd174ae63044eaab9742755259fd) `docs(bamf): repair C16.1a R13 reconciliation finding`
- [`ae988346d471`](https://github.com/Entif-AI/Bilqis-MLX/commit/ae988346d471d94c61140f8bbee27f5a0535625c) `docs(bamf): checkpoint C16.1a R14 review gate`
- [`08654dd2efd1`](https://github.com/Entif-AI/Bilqis-MLX/commit/08654dd2efd199cda03527bc456c3631f3cc0dbb) `fix(bamf): close exact two-site motif discriminator (PR #975 / BAMF-0.2 B08.5)`
- [`269f4d040514`](https://github.com/Entif-AI/Bilqis-MLX/commit/269f4d04051493f5e68ce7d6164aacc7bdb0390c) `test(bamf): prove source adapter execution (#863)`
- [`4d62864d3ccc`](https://github.com/Entif-AI/Bilqis-MLX/commit/4d62864d3ccc5e2f75bb9ecbce9f7f6b11644868) `docs(bamf): turn in B05.2a #863`
- [`4d7599086c2a`](https://github.com/Entif-AI/Bilqis-MLX/commit/4d7599086c2aed283a25ac24f6cc35271f4dc9ce) `feat(bamf): prove source-backed adapter execution (closes #863 / BAMF-0.2 B05.2a / PR #981 / Refs #450)`
- [`83bdcf9485d9`](https://github.com/Entif-AI/Bilqis-MLX/commit/83bdcf9485d9a39abe35da07b49bc62bbecb521d) `docs(bamf): reconcile B05.2 integrated closeout`
- [`36c4bcb4adc5`](https://github.com/Entif-AI/Bilqis-MLX/commit/36c4bcb4adc51e3eb9139f5580df2080e9c94ef3) `docs(bamf): repair C16.1a R14 review findings`
- [`8b8625b85b57`](https://github.com/Entif-AI/Bilqis-MLX/commit/8b8625b85b571ae1eeecbc683157895db029a812) `feat(bamf): reconcile integrated closeout receipt (BAMF-0.2 B05.2 / PR #982 / #450)`
- [`5c7b5fd1677a`](https://github.com/Entif-AI/Bilqis-MLX/commit/5c7b5fd1677a4ec1a7046c1a22511a066a132778) `docs(bamf): checkpoint C16.1a R15 review gate`
- [`731286ef7f00`](https://github.com/Entif-AI/Bilqis-MLX/commit/731286ef7f0041dd821a23ac5a6cc789a6a96f7e) `test(bamf): reconcile B13 parent integration (#372)`
- [`c1d88064544f`](https://github.com/Entif-AI/Bilqis-MLX/commit/c1d88064544fefcf6ecabcf4f3d099a6ebf6a560) `docs(bamf): repair C16.1a R16 design gate`
- [`577b6621f7fd`](https://github.com/Entif-AI/Bilqis-MLX/commit/577b6621f7fd32cd513adcee7ec3a92d2561c5a1) `docs(bamf): checkpoint C16.1a R16 review gate`
- [`95e8cc1abfb9`](https://github.com/Entif-AI/Bilqis-MLX/commit/95e8cc1abfb951a2954ffd39e7d2a3dad40ab2af) `docs(bamf): turn in B13 parent #372`
- [`50cd02711641`](https://github.com/Entif-AI/Bilqis-MLX/commit/50cd02711641add31415d2c9b17369933fb49fb0) `fix(bamf): reconcile parent integration witnesses (BAMF-0.2 B13 / PR #983)`
- [`52c6a5aab184`](https://github.com/Entif-AI/Bilqis-MLX/commit/52c6a5aab184fa1df462791260adb1de5bd4ca38) `feat(bamf): admit capability-only factory successors (#955)`
- [`4ee6e0eb3695`](https://github.com/Entif-AI/Bilqis-MLX/commit/4ee6e0eb36951471d24f6c8def85a4f7bcfe2290) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/955-c07-capability-only-r4-20261110`
- [`a767a5b4666b`](https://github.com/Entif-AI/Bilqis-MLX/commit/a767a5b4666b9b5cb4e67c5e8a4762e1a23c750c) `docs(bamf): repair C16.1a R17 design gate`
- [`02a44396f20b`](https://github.com/Entif-AI/Bilqis-MLX/commit/02a44396f20bcab3c9c41dcf001f7cbd723ca389) `docs(bamf): checkpoint C16.1a R17 review gate`
- [`b191e09763d2`](https://github.com/Entif-AI/Bilqis-MLX/commit/b191e09763d2e8cbca3c7c8addb24f02641d3163) `fix(bamf): serialize v2 lease publication (#955)`
- [`76a2e8e25644`](https://github.com/Entif-AI/Bilqis-MLX/commit/76a2e8e25644f86a5b2f0c751e5c4904e16d4fd3) `test(bamf): split capability publication fixture (#955)`
- [`75f6bd502737`](https://github.com/Entif-AI/Bilqis-MLX/commit/75f6bd50273791d1406038fc3241c1c2993d754f) `docs(bamf): repair C16.1a R18 design gate`
- [`b4ada021cb45`](https://github.com/Entif-AI/Bilqis-MLX/commit/b4ada021cb45de137b968b8c972a412176265f36) `docs(bamf): checkpoint C16.1a R18 review gate`
- [`51cda75bf7e7`](https://github.com/Entif-AI/Bilqis-MLX/commit/51cda75bf7e75e84533605bf0375789aac14a814) `docs(bamf): repair C16.1a R19 design gate`
- [`3212531a8510`](https://github.com/Entif-AI/Bilqis-MLX/commit/3212531a851074d196dc615c55d28b71c264e2f7) `docs(bamf): checkpoint C16.1a R19 review gate`
- [`f547cfa64e50`](https://github.com/Entif-AI/Bilqis-MLX/commit/f547cfa64e5070ba3b0a7bb189f093bcf86a3045) `refactor(bamf): split generation-zero recovery ownership`
- [`aec778c2271b`](https://github.com/Entif-AI/Bilqis-MLX/commit/aec778c2271bf6cc70dab4dd0315bae826a3be6c) `feat(bamf): serialize C07 authority and run-root claims`
- [`ebe8c7fb90d6`](https://github.com/Entif-AI/Bilqis-MLX/commit/ebe8c7fb90d61e724b974c7b6cf20b3456b28673) `feat(bamf): harden B13 genesis durability and path custody`
- [`2a9c908d8185`](https://github.com/Entif-AI/Bilqis-MLX/commit/2a9c908d8185e3abfeadcaa893df4fd66cad5674) `feat(bamf): own accepted Atlas v2 enrollment in C07`
- [`b398d190631c`](https://github.com/Entif-AI/Bilqis-MLX/commit/b398d190631c7829fbe78024f94214f20e36cf22) `feat(bamf): route C16.1a lifecycle without learner`
- [`593c427b30e6`](https://github.com/Entif-AI/Bilqis-MLX/commit/593c427b30e6516bc8694d3fab59e0a54a86122a) `fix(bamf): retain source-qualified motif allocations`
- [`1772af7f606d`](https://github.com/Entif-AI/Bilqis-MLX/commit/1772af7f606def85b81ab7b50ba6ea9f71bd231c) `test(bamf): prove persisted C16.1a first start`
- [`b041a4f19370`](https://github.com/Entif-AI/Bilqis-MLX/commit/b041a4f19370e422f19894d01c26aa1ab8df3108) `test(bamf): preserve cold-trust failure ordering`
- [`4c6f62a73898`](https://github.com/Entif-AI/Bilqis-MLX/commit/4c6f62a73898f18095fc94da5bb7bec569a617f6) `refactor(bamf): split sealed genesis recovery`
- [`a1ac6c27e250`](https://github.com/Entif-AI/Bilqis-MLX/commit/a1ac6c27e250063baf9ce1e44c98ada2e2087b1c) `docs(bamf): checkpoint C16.1a implementation review`
- [`0b4e2aa378a0`](https://github.com/Entif-AI/Bilqis-MLX/commit/0b4e2aa378a008498ed983c1d788ba644588a717) `fix(bamf): route lifecycle errors through control plane`
- [`a04a324f6cc9`](https://github.com/Entif-AI/Bilqis-MLX/commit/a04a324f6cc90e95b5c7a1da3d6ab627e3878606) `docs(bamf): checkpoint C16.1a turn-in head`
- [`ce085f1451e0`](https://github.com/Entif-AI/Bilqis-MLX/commit/ce085f1451e0fc6b9c12673fb6b48de347ab96c1) `fix(bamf): harden retained motif allocation authority`
- [`5c2df338400c`](https://github.com/Entif-AI/Bilqis-MLX/commit/5c2df338400cde252e034d6f2fac82e700be8b0a) `refactor(bamf): split custody ownership modules`
- [`ab8050b0b5e3`](https://github.com/Entif-AI/Bilqis-MLX/commit/ab8050b0b5e34a193870c72b8b63a08c163065e2) `refactor(bamf): split motif allocation review seams`
- [`08ec88eab9ae`](https://github.com/Entif-AI/Bilqis-MLX/commit/08ec88eab9ae638fe2ee53a582e422a602aee7ef) `fix(bamf): name source authority issuance records`
- [`1ad52f7932a2`](https://github.com/Entif-AI/Bilqis-MLX/commit/1ad52f7932a2605a6abc31c80ead3cf06000bc2e) `fix(bamf): defer motif materializer import`
- [`036e0aa3c2be`](https://github.com/Entif-AI/Bilqis-MLX/commit/036e0aa3c2bec184481a4f009d8c31e16b9495f5) `feat(bamf): retain source-qualified motif allocations (BAMF-0.2 B07)`
- [`bcdec584c9e1`](https://github.com/Entif-AI/Bilqis-MLX/commit/bcdec584c9e1eacfbd66c8c2e67dab1e76463ecd) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/955-c07-capability-only-r4-20261110`
- [`5c2b10c34bda`](https://github.com/Entif-AI/Bilqis-MLX/commit/5c2b10c34bda27d69468ea80198536dd54795eb3) `refactor(bamf): split merged acceptance validation (#955)`
- [`41d18a666d5c`](https://github.com/Entif-AI/Bilqis-MLX/commit/41d18a666d5ccbbb7ee33e39fd5db79fa5881e9e) `refactor(bamf): split publication acceptance authority (#955)`
- [`e1eb4f4c8220`](https://github.com/Entif-AI/Bilqis-MLX/commit/e1eb4f4c8220a941aa6a5b099c8ed9a75792c99f) `style(bamf): normalize publication authority eof (#955)`
- [`896b38ea86cf`](https://github.com/Entif-AI/Bilqis-MLX/commit/896b38ea86cf16739a4ad7fe436f67c3e1d50ff8) `fix(bamf): disambiguate v3 custody transitions (#955)`
- [`57ab58334bc1`](https://github.com/Entif-AI/Bilqis-MLX/commit/57ab58334bc1903559d01cc543a4511c5d644fb2) `fix(bamf): bind atomic training prefixes to delivered source rows`
- [`39eeefea431e`](https://github.com/Entif-AI/Bilqis-MLX/commit/39eeefea431e19bbc88d35d30ffb4a223340a344) `fix(bamf): reconcile B06 refinement tensor registry (#455)`
- [`b39a02e72862`](https://github.com/Entif-AI/Bilqis-MLX/commit/b39a02e728620ecebbe25cbc9392d1759d3d498f) `feat(bamf): bind C06 salience evidence to candidate gradients`
- [`8a4886e872d8`](https://github.com/Entif-AI/Bilqis-MLX/commit/8a4886e872d8bebd81ea7833084b6111b79dd6d9) `test(bamf): preserve raw C06 red evidence without whitespace debt`
- [`f3ab5384ba5f`](https://github.com/Entif-AI/Bilqis-MLX/commit/f3ab5384ba5ff8be9c1ab6463e1f90e7ab5f4da2) `docs(bamf): record B06.4 current-unified proof (#455)`
- [`888d9f22192d`](https://github.com/Entif-AI/Bilqis-MLX/commit/888d9f22192d504c8838688893976d38657f7cba) `test(bamf): serialize staged C06 Studio qualification`
- [`7790f0c86afd`](https://github.com/Entif-AI/Bilqis-MLX/commit/7790f0c86afde5b7bdcb4d8ecbb7fc9c7194694d) `fix(bamf): derive complete frame inventory from source authority`
- [`e0dc9bfb35c4`](https://github.com/Entif-AI/Bilqis-MLX/commit/e0dc9bfb35c45e71c01363825f7819247013e1e9) `test(bamf): reject skipped C06 Studio evidence`
- [`45ade913d1f6`](https://github.com/Entif-AI/Bilqis-MLX/commit/45ade913d1f67b7b509e35fc7c214de75f4eb3d9) `docs(bamf): record A13 source inventory review and proof`
- [`7452fc9ef07b`](https://github.com/Entif-AI/Bilqis-MLX/commit/7452fc9ef07bb53260e46b84e4b588e0beae8f93) `fix(bamf): close C16.1a lifecycle review gaps`
- [`c2e65c292322`](https://github.com/Entif-AI/Bilqis-MLX/commit/c2e65c2923220ccf7ecb0edcc29dc1c8a31dd235) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/bamf02-c-runtime`
- [`7228f7fa8162`](https://github.com/Entif-AI/Bilqis-MLX/commit/7228f7fa8162bfbf61926bce9d01c54c440baff9) `refactor(bamf): compartmentalize Atlas lease tests`
- [`bd59251a7c24`](https://github.com/Entif-AI/Bilqis-MLX/commit/bd59251a7c24aa1b47609ab0dcd56b4611b40b4f) `fix(bamf): bind B14 cache to accepted custody`
- [`f8f61dc16742`](https://github.com/Entif-AI/Bilqis-MLX/commit/f8f61dc1674269c323ddd55258df88069033fce6) `fix(bamf): seal B06 projection authority (#455)`
- [`2c5b4be69d49`](https://github.com/Entif-AI/Bilqis-MLX/commit/2c5b4be69d493e07e654ffaf45fee3aa0004d14d) `docs(bamf): refresh B06.4 repair receipt (#455)`
- [`ac953de1a57e`](https://github.com/Entif-AI/Bilqis-MLX/commit/ac953de1a57e9534af7e986735ad6e64ed790933) `fix(bamf): defer v2 adoption policy imports (#955)`
- [`880d9d67e055`](https://github.com/Entif-AI/Bilqis-MLX/commit/880d9d67e055f64e74db926618482e2a5092f917) `fix(bamf): preserve late-bound v2 verifier seam (#955)`
- [`40873f2a6c4e`](https://github.com/Entif-AI/Bilqis-MLX/commit/40873f2a6c4e7f766c7a973b084a7924f89b2108) `refactor(bamf): keep Atlas lease tests canonical`
- [`4d133897f625`](https://github.com/Entif-AI/Bilqis-MLX/commit/4d133897f625d78ef0398b2902511af0a980cf1a) `test(bamf): compartment B14 cache witnesses`
- [`cff35bb382ef`](https://github.com/Entif-AI/Bilqis-MLX/commit/cff35bb382efb946a35ed965cad545c92d86af0b) `docs(bamf): record final B06.4 qualification (#455)`
- [`ee58220e8354`](https://github.com/Entif-AI/Bilqis-MLX/commit/ee58220e8354bb17f70f52d57adbc36c0bb80f05) `docs(bamf): turn in B06.4 registry reconciliation (#455)`
- [`08ae3d5f0f4e`](https://github.com/Entif-AI/Bilqis-MLX/commit/08ae3d5f0f4e2420bc230dee843a86cb05f489fe) `fix(bamf): avoid duplicate B06.4 mitigation PR ownership (#455)`
- [`d038b1e26403`](https://github.com/Entif-AI/Bilqis-MLX/commit/d038b1e264039ebc067b56849557746e6cbd6c4b) `fix(bamf): satisfy C16.1a final review contracts`
- [`e69e61299eea`](https://github.com/Entif-AI/Bilqis-MLX/commit/e69e61299eea2ba33d6ad2b4aa211e4bbbbbf244) `refactor(bamf): name B14 cache guard constants`
- [`662d303a8f6b`](https://github.com/Entif-AI/Bilqis-MLX/commit/662d303a8f6b4458726e17a8de7a05a73d9fc3be) `docs(bamf): checkpoint C16.1a review candidate`
- [`3e1957eb976d`](https://github.com/Entif-AI/Bilqis-MLX/commit/3e1957eb976de033078235d6bed49f088fcd9203) `refactor(bamf): compartmentalize lifecycle witnesses`
- [`dd63880fdfde`](https://github.com/Entif-AI/Bilqis-MLX/commit/dd63880fdfde9d01eccbbff876e39828dbded3f6) `refactor(bamf): keep B14 cache bridge bounded`
- [`11b7338a41bf`](https://github.com/Entif-AI/Bilqis-MLX/commit/11b7338a41bf8d391eadb205959c7bc81d30ca97) `docs(bamf): checkpoint final C16.1a candidate`
- [`53c090e62810`](https://github.com/Entif-AI/Bilqis-MLX/commit/53c090e62810ce82a0934048adc88ff60504670a) `test(bamf): close C16.1a acceptance proof gaps`
- [`abc78f8b0144`](https://github.com/Entif-AI/Bilqis-MLX/commit/abc78f8b01444db39bfc55fc0e94289c73c5111b) `docs(bamf): checkpoint reviewed C16.1a proof`
- [`5166aca71f01`](https://github.com/Entif-AI/Bilqis-MLX/commit/5166aca71f01f09cfb4e533d61dc41e53a987726) `feat(bamf): bind derived cache to accepted B13 custody (BAMF-0.2 B14)`
- [`766ac5f1a942`](https://github.com/Entif-AI/Bilqis-MLX/commit/766ac5f1a94202ce1048bcda0c1a2c5cbefec642) `feat(bamf): reconcile refinement tensors with B01 registry (BAMF-0.2 B06.4)`
- [`2b5644e37ffb`](https://github.com/Entif-AI/Bilqis-MLX/commit/2b5644e37ffbecb9fa5ad49a1c33ced2d14e4d1d) `fix(bamf): close final C16.1a review gaps`
- [`09f5df3da8fb`](https://github.com/Entif-AI/Bilqis-MLX/commit/09f5df3da8fbdedc800722ff3c5256971f8873ca) `docs(bamf): refresh C16.1a verification receipts`
- [`f9b2862833b8`](https://github.com/Entif-AI/Bilqis-MLX/commit/f9b2862833b8ebfe58e51aa422a64b3a0421cde9) `docs(bamf): checkpoint final C16.1a review object`
- [`b90dd5c67b31`](https://github.com/Entif-AI/Bilqis-MLX/commit/b90dd5c67b318d0c6f51558d2047b9d37af5fbac) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/354-a13-prefix-inventory-20261107`
- [`e58bd2fe2559`](https://github.com/Entif-AI/Bilqis-MLX/commit/e58bd2fe2559fe2f345cde965c161af263510f6f) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/955-c07-capability-only-r4-20261110`
- [`24614b134def`](https://github.com/Entif-AI/Bilqis-MLX/commit/24614b134def0afa9e6886782d1a9424efb197d4) `fix(bamf): preserve historical topology routing`
- [`7a4528e84d2c`](https://github.com/Entif-AI/Bilqis-MLX/commit/7a4528e84d2c77f8ae17a6c7136451791912a456) `docs(bamf): checkpoint C16.1a rereview candidate`
- [`6508db3d1dce`](https://github.com/Entif-AI/Bilqis-MLX/commit/6508db3d1dcefb372218e203463fa846b6f66d4c) `test(bamf): close C07.1c proof gaps (#955)`
- [`caea8d555688`](https://github.com/Entif-AI/Bilqis-MLX/commit/caea8d555688d28bd1b5a3615e41348dcd138db7) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/bamf02-c-runtime`
- [`04a3e4375420`](https://github.com/Entif-AI/Bilqis-MLX/commit/04a3e4375420acce07d9a39ff5403fa48a22232b) `refactor(bamf): compartment C07.1c proof fixture (#955)`
- [`1b24f94f5933`](https://github.com/Entif-AI/Bilqis-MLX/commit/1b24f94f59338b1344bb10ad9409d8d373855f16) `test(bamf): prove B06 parent acceptance (#365)`
- [`02123dbaf45f`](https://github.com/Entif-AI/Bilqis-MLX/commit/02123dbaf45f69f6ee5c47307f75efedb9452170) `docs(bamf): record B06 parent gate evidence (#365)`
- [`f43bb4d84aee`](https://github.com/Entif-AI/Bilqis-MLX/commit/f43bb4d84aee5dde5307f236fad29994c4f9743b) `docs(bamf): bind B06 base-owned fixture debt (#365)`
- [`e89d305bcd41`](https://github.com/Entif-AI/Bilqis-MLX/commit/e89d305bcd41b104a6b0e8a398a33ab7a728bbb7) `docs(bamf): classify B06 parent drift (#365)`
- [`75a9aee0c4f6`](https://github.com/Entif-AI/Bilqis-MLX/commit/75a9aee0c4f6d15dc3e4f91c350f72b991284396) `docs(bamf): avoid false B06 trainer-authority trigger (#365)`
- [`c3cf6f87f0e6`](https://github.com/Entif-AI/Bilqis-MLX/commit/c3cf6f87f0e6591caf195487da8f9d6f5cb90bf8) `docs(bamf): checkpoint C16.1a post-sync proof`
- [`074cf2421fc4`](https://github.com/Entif-AI/Bilqis-MLX/commit/074cf2421fc41a54ac05ead490463b49435ab7aa) `docs(bamf): refresh Lane C reviewed-unified receipt`
- [`c22a8ea889a0`](https://github.com/Entif-AI/Bilqis-MLX/commit/c22a8ea889a0f41269cdb4cdb20bbe89269bd383) `feat(bamf): prove parent acceptance (BAMF-0.2 B06)`
- [`edb004e8d7dd`](https://github.com/Entif-AI/Bilqis-MLX/commit/edb004e8d7dd982c5761533ef017128db0144d53) `feat(bamf): persistent BAMF create dry-run and resume entrypoints (BAMF-0.2 C16.1a)`
- [`2bc05363dfb6`](https://github.com/Entif-AI/Bilqis-MLX/commit/2bc05363dfb60eb2dbe872dc86f3734cf6b28bee) `test(bamf): prove B09 grade-neutral retained state`
- [`f6963d0c75ea`](https://github.com/Entif-AI/Bilqis-MLX/commit/f6963d0c75ea89b8cf92ee4883b417c2264a32f2) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/368-b09-parent-acceptance-20261111`
- [`7060ea92b956`](https://github.com/Entif-AI/Bilqis-MLX/commit/7060ea92b9560d259743fe9b4117284b77ec27e2) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/955-c07-capability-only-r4-20261110`
- [`df52a83ab44a`](https://github.com/Entif-AI/Bilqis-MLX/commit/df52a83ab44aadcf61ae2f20cac9113ca6a80dd1) `fix(bamf): reconcile C07 proof imports after unified merge (#955)`
- [`f2d0dab40ede`](https://github.com/Entif-AI/Bilqis-MLX/commit/f2d0dab40ede4f7f3ad5b3af473b79a90a34e5cb) `test(bamf): close B09 parent proof gaps`
- [`2680932bd560`](https://github.com/Entif-AI/Bilqis-MLX/commit/2680932bd560ea0bfb786a8f6f120b5054af4c52) `docs(bamf): activate C16.2 learning readiness (#544)`
- [`74884a4f292b`](https://github.com/Entif-AI/Bilqis-MLX/commit/74884a4f292b005491bfe1b59075411a3490e7fa) `refactor(bamf): compartment merged Atlas admission surface (#955)`
- [`091dbafd57e3`](https://github.com/Entif-AI/Bilqis-MLX/commit/091dbafd57e35169ccd5012438290ad7223e93ce) `docs(bamf): record B09 parent acceptance`
- [`21833d5513f6`](https://github.com/Entif-AI/Bilqis-MLX/commit/21833d5513f676edceb4e6e7eeeeb7199af271a0) `docs(bamf): refresh C07 merged error catalog (#955)`
- [`f9aa79b6cece`](https://github.com/Entif-AI/Bilqis-MLX/commit/f9aa79b6cececdedd28a0e80db1256f8a70a9d7f) `feat(bamf): prove parent grade-neutral retained state (BAMF-0.2 B09)`
- [`add82428ac6b`](https://github.com/Entif-AI/Bilqis-MLX/commit/add82428ac6bc0c78c8c59e29287c81d69b8e2d1) `C08: bind logical batch accumulation to resource plan (#374)`
- [`61bff099ee36`](https://github.com/Entif-AI/Bilqis-MLX/commit/61bff099ee36757547f4c2315e9d2d63c5990af4) `docs(bamf): design C16.2 launch readiness (#544)`
- [`089bdb5637a6`](https://github.com/Entif-AI/Bilqis-MLX/commit/089bdb5637a6ee8d1c9adb2f53d76bc70870d41b) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/544-c16-learning-readiness-20261111`
- [`7f953ee7be4d`](https://github.com/Entif-AI/Bilqis-MLX/commit/7f953ee7be4d973e6dc0bcd074de73f5eb6ef9c3) `fix(bamf): close C08 review gaps`
- [`62d2ca46f1f3`](https://github.com/Entif-AI/Bilqis-MLX/commit/62d2ca46f1f34e8dbafe7d6289fd8f56740dfae5) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/955-c07-capability-only-r4-20261110`
- [`71be89913e20`](https://github.com/Entif-AI/Bilqis-MLX/commit/71be89913e203ec35ee197d15b0e09ab87b12e15) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/354-a13-prefix-inventory-20261107`
- [`96159c096f73`](https://github.com/Entif-AI/Bilqis-MLX/commit/96159c096f73f5fa3ecf31ea3bae47144592d8cf) `test(bamf): strengthen C08 drift proofs`
- [`f25edba4fe56`](https://github.com/Entif-AI/Bilqis-MLX/commit/f25edba4fe56c77cdb68e2191091da1b7260143f) `test(bamf): split C08 candidate-step proofs`
- [`88bdf6a1547c`](https://github.com/Entif-AI/Bilqis-MLX/commit/88bdf6a1547cde91c6ce8e508b9a2bb0559435c3) `docs(bamf): preserve current unified quality provenance`
- [`9a4ee7079896`](https://github.com/Entif-AI/Bilqis-MLX/commit/9a4ee7079896a175f9c5ae713fb1570aa8f9e2b2) `feat(bamf): bind generation-zero Factory custody (C16.2a)`
- [`7d1ce49d4c75`](https://github.com/Entif-AI/Bilqis-MLX/commit/7d1ce49d4c754d3584c49a99a62a8a60c1f8f14f) `test(bamf): restore C07.1c amendment proof matrix (#955)`
- [`665e67f2f440`](https://github.com/Entif-AI/Bilqis-MLX/commit/665e67f2f44023dd7cc615d04a6a118effca5e1e) `fix(bamf): scope C07 retry predecessor checks (#955)`
- [`b758ed90f41a`](https://github.com/Entif-AI/Bilqis-MLX/commit/b758ed90f41a5b18f4eb0e47b706f546f159d2a1) `docs: bound MLX verification resources`
- [`a3bd22c2fb0a`](https://github.com/Entif-AI/Bilqis-MLX/commit/a3bd22c2fb0a0c10da7e3578125ed8c072ef2479) `docs(bamf): refresh A13 final gate status`
- [`ea4cb09653dc`](https://github.com/Entif-AI/Bilqis-MLX/commit/ea4cb09653dc42b5e429a7225f1a8daf7a506321) `fix(bamf): stabilize C07 v2 historical retry (#955)`
- [`9b170cbf93de`](https://github.com/Entif-AI/Bilqis-MLX/commit/9b170cbf93de08e0a83242e9d331ffb5ebd7a3e3) `fix(bamf): validate Factory delivery observations`
- [`7a9c88c65dff`](https://github.com/Entif-AI/Bilqis-MLX/commit/7a9c88c65dff6d2cb677e1735ce815dd291efb42) `test(bamf): preserve v2 negative witness context (#955)`
- [`1c4e15970a5f`](https://github.com/Entif-AI/Bilqis-MLX/commit/1c4e15970a5f90eb5022206430f9b9ffc291d36e) `feat(bamf): give C05 native fixed-school custody (C16.2b)`
- [`59ea53570ccf`](https://github.com/Entif-AI/Bilqis-MLX/commit/59ea53570ccf7b3084c90224b7b146d2d5bae892) `test(bamf): bind C09 authority through C05 live witness`
- [`ddb8b6f73f8d`](https://github.com/Entif-AI/Bilqis-MLX/commit/ddb8b6f73f8d526d3eb6a3ff813d9dec252fca9c) `docs(bamf): reconcile C16.2 after EGM decomposition`
- [`7ff8694f8cb8`](https://github.com/Entif-AI/Bilqis-MLX/commit/7ff8694f8cb81d35ecc462b6eab777afef990d3d) `test(bamf): repair moved Atlas lease helper imports (#955)`
- [`97891e26b947`](https://github.com/Entif-AI/Bilqis-MLX/commit/97891e26b947d5eaf4b0133a6f58d6d409e03b39) `refactor(bamf): restore C05 owner structure limits`
- [`4dba6a19398b`](https://github.com/Entif-AI/Bilqis-MLX/commit/4dba6a19398b8e51b02b78155b6c6add34e05412) `test(bamf): repair moved Factory retention imports`
- [`64b85e7a2ebc`](https://github.com/Entif-AI/Bilqis-MLX/commit/64b85e7a2ebc2a64efb177e58de959e4b8950e41) `test(bamf): preflight C08 Factory witness`
- [`422972983446`](https://github.com/Entif-AI/Bilqis-MLX/commit/422972983446d35299aef1a05695cc8b60c1502b) `docs(bamf): require staged expensive-test preflight`
- [`5d0c5ac20913`](https://github.com/Entif-AI/Bilqis-MLX/commit/5d0c5ac20913bd3d7b9f1dd69e1922a065bdf532) `test(bamf): synthesize accepted v2 lease drift witness (#955)`
- [`d2f1dde814bb`](https://github.com/Entif-AI/Bilqis-MLX/commit/d2f1dde814bbcb6bab49da7ec3368e6b3fe32370) `fix(bamf): seal C05 fixed-school custody (#993)`
- [`5572b0c503ff`](https://github.com/Entif-AI/Bilqis-MLX/commit/5572b0c503ff6703f7450ff93df70455da737179) `test(bamf): preserve A02 policy row maturation witness (#955)`
- [`66573d4b5b56`](https://github.com/Entif-AI/Bilqis-MLX/commit/66573d4b5b56048723d4c20b948520ddacab0f04) `test(bamf): prove C16.2 launch readiness (#994)`
- [`7d9f11396e4f`](https://github.com/Entif-AI/Bilqis-MLX/commit/7d9f11396e4f7ec890b709ed4a4a8184b8b95dfb) `fix(bamf): ignore runtime runs in detached mutation guard`
- [`23b279bfca68`](https://github.com/Entif-AI/Bilqis-MLX/commit/23b279bfca68a284e1a219cdd094d0072f823440) `docs(bamf): classify A13 final gate against unified`
- [`8cd1094361c9`](https://github.com/Entif-AI/Bilqis-MLX/commit/8cd1094361c94025171b908ef7d8cb60b226463b) `test(bamf): harden staged C08 verification`
- [`a79a19866c31`](https://github.com/Entif-AI/Bilqis-MLX/commit/a79a19866c313c019ad022ae234f40b318c4c708) `docs(bamf): record C08 parent acceptance`
- [`324182a1c889`](https://github.com/Entif-AI/Bilqis-MLX/commit/324182a1c8899a179bbf539f926f3f4ad732c188) `feat(bamf): enforce combined context eligibility before neural or motif access (BAMF-0.2 A13)`
- [`c42362ced030`](https://github.com/Entif-AI/Bilqis-MLX/commit/c42362ced0309a24f2f95391257df8f4ef3588cc) `feat(bamf): admit capability-only Factory successors without neural mutation (BAMF-0.2 C07.1c)`
- [`df58bc023a50`](https://github.com/Entif-AI/Bilqis-MLX/commit/df58bc023a50591279c7219ae2ca8ae1b8abb8e0) `feat(bamf): checkpoint C06 bootstrap repair and partial closure custody`
- [`d54b0703f66b`](https://github.com/Entif-AI/Bilqis-MLX/commit/d54b0703f66beda6e60f12c1de58c07885e28026) `merge(bamf): reconcile C08 with current unified base`
- [`66c6850c0530`](https://github.com/Entif-AI/Bilqis-MLX/commit/66c6850c0530e9c0a497473f453f0d188b4baab1) `docs(bamf): record C08 current-base reconciliation`
- [`a6b52176f147`](https://github.com/Entif-AI/Bilqis-MLX/commit/a6b52176f14742ec1e43e15631d485f49176f8ab) `feat(bamf): connect accepted priority visits and retained salience custody`
- [`e3486f132f9e`](https://github.com/Entif-AI/Bilqis-MLX/commit/e3486f132f9e18b891c7c4f4b9d709af5082efa8) `chore(c06): integrate current unified lifecycle contracts`
- [`13c131e1da96`](https://github.com/Entif-AI/Bilqis-MLX/commit/13c131e1da9692256e903b2a9e7365c7678a81eb) `feat(bamf): partial progress on #379 (C06)`
- [`1d9866b5c93c`](https://github.com/Entif-AI/Bilqis-MLX/commit/1d9866b5c93cefa08c2fcb790261ccf2716a5e38) `docs(bamf): record C08 final review disposition`
- [`25e04ca5819f`](https://github.com/Entif-AI/Bilqis-MLX/commit/25e04ca5819fef61e15f9f89cf98df8aa65395e8) `test(bamf): bind C06 retained publication witness`
- [`d396fcd95407`](https://github.com/Entif-AI/Bilqis-MLX/commit/d396fcd95407135d3e8631ffda37be678f323790) `test(bamf): prove C07 repeated lease adoption (#509)`
- [`e7423f0baca6`](https://github.com/Entif-AI/Bilqis-MLX/commit/e7423f0baca688744327fd5e37d2283dc2965181) `test(bamf): cap concurrent C06 Studio proof at 24 GiB`
- [`d97ab0c16da6`](https://github.com/Entif-AI/Bilqis-MLX/commit/d97ab0c16da67defd9abb087fa3ac8a9050bc590) `test(bamf): refresh C06 frontier fixture in disposable custody`
- [`049aec098cbc`](https://github.com/Entif-AI/Bilqis-MLX/commit/049aec098cbc97e1db9dee1fd1b015af451bb82c) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/544-c16-learning-readiness-20261111`
- [`bc9371846dba`](https://github.com/Entif-AI/Bilqis-MLX/commit/bc9371846dbad88ff20a50cc686bf4946072f306) `test(bamf): stage C16.2c verification by proof obligation`
- [`be5abceb21e1`](https://github.com/Entif-AI/Bilqis-MLX/commit/be5abceb21e167e813952994821c4535d9a7fd68) `test(bamf): allow concurrent C16.2c M3 verification`
- [`6c2e4a2429cc`](https://github.com/Entif-AI/Bilqis-MLX/commit/6c2e4a2429cc20e4d90af07206c0d5ddad8273d4) `docs(bamf): fail fast before expensive C08 turn-in`
- [`96fc890068a2`](https://github.com/Entif-AI/Bilqis-MLX/commit/96fc890068a2ee55589c2bd198c3fb4a3cab1091) `test(bamf): handle immutable optimizer trees in C07 witness`
- [`416b4374cd07`](https://github.com/Entif-AI/Bilqis-MLX/commit/416b4374cd07efabe00dc17004039bd0806e8e7b) `fix(testing): keep detached witnesses out of aggregate gate`
- [`d440895b3279`](https://github.com/Entif-AI/Bilqis-MLX/commit/d440895b3279acbe33d1d4ff08591e23b5832755) `fix(testing): bind Factory correction fixture authority`
- [`9fe399635c07`](https://github.com/Entif-AI/Bilqis-MLX/commit/9fe399635c074b8137de0cbbc24de767eaca547d) `docs(bamf): allow bounded M3 Ultra MLX concurrency`
- [`d50fb77f9a11`](https://github.com/Entif-AI/Bilqis-MLX/commit/d50fb77f9a116446d2f7a6462e97d606b9c3c455) `fix(testing): isolate Factory genesis trust state`
- [`3e0a02a3d34b`](https://github.com/Entif-AI/Bilqis-MLX/commit/3e0a02a3d34bc1fb06c1096519e9f0d78377f5a3) `fix(testing): close isolated Factory data planes`
- [`5adc8e18f7d8`](https://github.com/Entif-AI/Bilqis-MLX/commit/5adc8e18f7d8c133a1fbd072c7f49381100821e6) `docs(bamf): finalize C08 turn-in evidence`
- [`c2ed8adf3216`](https://github.com/Entif-AI/Bilqis-MLX/commit/c2ed8adf3216b548769d1741509264d2b4733934) `feat(bamf): topology-aware logical batch execution (BAMF-0.2 C08)`
- [`678a97f5d4bd`](https://github.com/Entif-AI/Bilqis-MLX/commit/678a97f5d4bdfe38721961bf22c896a84040bffb) `test(bamf): preserve C07 rows across vocabulary allocation`
- [`0b1bab11b7f1`](https://github.com/Entif-AI/Bilqis-MLX/commit/0b1bab11b7f1c8356791354f49cc6283330a08ef) `test(bamf): keep repeated C07 event targets parameter-only`
- [`e7b680ada8f5`](https://github.com/Entif-AI/Bilqis-MLX/commit/e7b680ada8f561e46562cf2897b1aa6ffed025d5) `test(factory): expose cold atlas replay duplication`
- [`a37d1db696a4`](https://github.com/Entif-AI/Bilqis-MLX/commit/a37d1db696a477e6167f5f419f6508059445e16f) `fix(factory): recover accepted atlas credit on cold replay`
- [`5d66eb1fbe49`](https://github.com/Entif-AI/Bilqis-MLX/commit/5d66eb1fbe49b1154a7d3189c2c1fd3368331d8e) `refactor(runtime): split exam execution ownership`
- [`edd987a6d2f1`](https://github.com/Entif-AI/Bilqis-MLX/commit/edd987a6d2f139da353a7c4411bbd0541bb6fe1a) `feat(bamf): make B11 diagnostics opt-in`
- [`11edd978b706`](https://github.com/Entif-AI/Bilqis-MLX/commit/11edd978b70612dfb140273d96642cdd80e9e570) `revert(runtime): drop out-of-scope exam split`
- [`b70eb8b6ee59`](https://github.com/Entif-AI/Bilqis-MLX/commit/b70eb8b6ee59fcb71e6ac58dca5cc507f1992601) `feat(bamf): unify direct inference gradient retention and championship dispatch (BAMF-0.2 B11.2)`
- [`a0fc99df2f98`](https://github.com/Entif-AI/Bilqis-MLX/commit/a0fc99df2f98daaf9cfcbbbf2a7784026cfea347) `test(atlas): expose repeated same-feature vocabulary append`
- [`f240a7d127d8`](https://github.com/Entif-AI/Bilqis-MLX/commit/f240a7d127d809f96aa3cb71b3b0d7f5fe4d7aa5) `fix(atlas): authenticate repeated same-feature vocabulary growth`
- [`f2a0e94befdf`](https://github.com/Entif-AI/Bilqis-MLX/commit/f2a0e94befdf2ec4cef125d0c3b65f5dc6eb57b5) `feat(bamf): reconcile mixed B11 tensor execution`
- [`63f87a1753c5`](https://github.com/Entif-AI/Bilqis-MLX/commit/63f87a1753c5b5f7e7a7dd9ef3dd72bb5ee06e3c) `feat(bamf): reconcile full model tensor prefixes and mixed-frame integration (BAMF-0.2 B11.3)`
- [`a11666f1f69d`](https://github.com/Entif-AI/Bilqis-MLX/commit/a11666f1f69dca8a0f2c60fbb5e9bbc1aad9540f) `test(bamf): close B11 integration proofs`
- [`b7389caa52c8`](https://github.com/Entif-AI/Bilqis-MLX/commit/b7389caa52c8ed2e849a5c98c92a7f6ca8510e08) `test(bamf): execute F05 through all layers`
- [`92cfbf6fb9ec`](https://github.com/Entif-AI/Bilqis-MLX/commit/92cfbf6fb9ec6ce97fa06a23405481c3ad51c7dc) `test(bamf): keep F05 helper debt-neutral`
- [`3d3e8962ddd0`](https://github.com/Entif-AI/Bilqis-MLX/commit/3d3e8962ddd0c61af2988b9d124fad1a94953a4a) `test(bamf): add compact C07 closure witness (#509)`
- [`cd213c729635`](https://github.com/Entif-AI/Bilqis-MLX/commit/cd213c72963519c19a3a36eb8e1442eb35d68718) `fix(bamf): close parent integration proof gaps (BAMF-0.2 B11.4)`
- [`d63f9cb60742`](https://github.com/Entif-AI/Bilqis-MLX/commit/d63f9cb60742f699f1549a4a3d11a27953235618) `test(bamf): make compact C07 witness A02-capable (#509)`
- [`286c023ffa8a`](https://github.com/Entif-AI/Bilqis-MLX/commit/286c023ffa8a02bf0a94a1784e0ab2d3df374e90) `merge reviewed unified into #509 closure`
- [`74aeb33db263`](https://github.com/Entif-AI/Bilqis-MLX/commit/74aeb33db2632fd7cee0b92bb0139d87f883d413) `test(bamf): detach C07 closure witness from aggregate gates (#509)`
- [`022994bde7a2`](https://github.com/Entif-AI/Bilqis-MLX/commit/022994bde7a2e83bcfe1cb6b808204950e390fd2) `fix(factory): bind cold atlas credit to accepted receipts (#509)`
- [`a7bd8cb45b3a`](https://github.com/Entif-AI/Bilqis-MLX/commit/a7bd8cb45b3ad2730625eaf1008c75cddf92833d) `fix(factory): bind staged obligations to frozen snapshot (#509)`
- [`eb79a098dad6`](https://github.com/Entif-AI/Bilqis-MLX/commit/eb79a098dad60ec5ff65abaaf68ad6d529b12f20) `fix(atlas): persist cold obligation credit in B13 (#509)`
- [`2f27a4e6e1f1`](https://github.com/Entif-AI/Bilqis-MLX/commit/2f27a4e6e1f1b26e60512ca17191b0ef73e5a81c) `chore(factory): name obligation key arity (#509)`
- [`2ddbb8b4be6b`](https://github.com/Entif-AI/Bilqis-MLX/commit/2ddbb8b4be6b9ffe8c84ae8c6b914565e4f3458d) `fix(atlas): verify v2 capability retry credit (#509)`
- [`7dfac223adbb`](https://github.com/Entif-AI/Bilqis-MLX/commit/7dfac223adbbcfba17dda3f87a03e298b734ca11) `refactor(bamf): split factory admission binding codec (#509)`
- [`e14138aaca8a`](https://github.com/Entif-AI/Bilqis-MLX/commit/e14138aaca8a1591ece060f7bae40db32a808ff7) `merge(bamf): sync C06 with current unified`
- [`db686f648b52`](https://github.com/Entif-AI/Bilqis-MLX/commit/db686f648b524e7f02f469dc56af98bf1ad41353) `test(bamf): bound C06 verification scope`
- [`81b95bacf82f`](https://github.com/Entif-AI/Bilqis-MLX/commit/81b95bacf82f41b19694594d14eb15dd1df40853) `docs(bamf): record bounded C06 turn-in evidence`
- [`5ef579c7578e`](https://github.com/Entif-AI/Bilqis-MLX/commit/5ef579c7578ed18e47cdd9b6567b5d94e7358114) `fix(bamf): retain C06 closure across C08 batches`
- [`e9052d2c8066`](https://github.com/Entif-AI/Bilqis-MLX/commit/e9052d2c80660f0080aadaa3019555f001d60dae) `docs(bamf): checkpoint C06 C08 closure repair`
- [`129a60ad0963`](https://github.com/Entif-AI/Bilqis-MLX/commit/129a60ad0963c6cc8668631c5d5b4146ed26fb31) `docs(bamf): record C06 turn-in review`
- [`812d945f57b6`](https://github.com/Entif-AI/Bilqis-MLX/commit/812d945f57b6a1f65781e8129da9900cdad243af) `feat(bamf): integrate SÍ SÉ SON salience into Factory priority and retained custody (BAMF-0.2 C06)`
- [`b2b150afa37a`](https://github.com/Entif-AI/Bilqis-MLX/commit/b2b150afa37a1fae72e89f2972958f1aabf6a351) `docs(governance): cap verification runs at two hours`
- [`f460d3ab3a47`](https://github.com/Entif-AI/Bilqis-MLX/commit/f460d3ab3a47740e8bdf131a8b500f98b5194d99) `docs(governance): record verification time ceiling`
- [`0d323cbc63b4`](https://github.com/Entif-AI/Bilqis-MLX/commit/0d323cbc63b49ffb905c5d8a9b1e728196b3378b) `docs(governance): cap verification test suites at two hours`
- [`ceb9409a1994`](https://github.com/Entif-AI/Bilqis-MLX/commit/ceb9409a199407809f5da948fab9c3d13acb34fc) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/509-c07-closure-20261111`
- [`47f991119b05`](https://github.com/Entif-AI/Bilqis-MLX/commit/47f991119b05b0bdfdc2bcf80b18390da27162b3) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/509-c07-closure-20261111`
- [`e274e5e9446b`](https://github.com/Entif-AI/Bilqis-MLX/commit/e274e5e9446b16a50878db87ad58ba5b5c70ec59) `test(atlas): bind parameter retry race to accepted v2 evidence (#509)`
- [`86505671713c`](https://github.com/Entif-AI/Bilqis-MLX/commit/86505671713c8086b6278850a36d014f51c4d0e2) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/544-c16-policy-sync-20261112`
- [`ee2e79f7f23c`](https://github.com/Entif-AI/Bilqis-MLX/commit/ee2e79f7f23c122edeca81dd871c64e5f97e1546) `test(bamf): retire over-budget C16.2c witness`
- [`88f7a2f620da`](https://github.com/Entif-AI/Bilqis-MLX/commit/88f7a2f620dab00a5d2d031700668c9a6bed0cb5) `test(bamf): close C07 parent acceptance proofs (#509)`
- [`8437bc3c7802`](https://github.com/Entif-AI/Bilqis-MLX/commit/8437bc3c78027463d564a31a04777e645d52d9d1) `test(bamf): split C07 capability verification suites (#509)`
- [`505dfdd1ea2c`](https://github.com/Entif-AI/Bilqis-MLX/commit/505dfdd1ea2cfe57d6e4418f7b6faed7428b71b6) `feat(bamf): close persisted atlas-admission lease and source scope (#509 / BAMF-0.2 C07.1a)`
- [`44a9216dad44`](https://github.com/Entif-AI/Bilqis-MLX/commit/44a9216dad441f67f6a11e96379d2dfad2f12dd9) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/544-c16-policy-sync-20261112`
- [`cb2441e63bf4`](https://github.com/Entif-AI/Bilqis-MLX/commit/cb2441e63bf4eea16a61a178d09e15850d534da3) `fix(bamf): close bounded turn-in quality debt`
- [`254a79f7352e`](https://github.com/Entif-AI/Bilqis-MLX/commit/254a79f7352eae0d5aec44ea38a3d6c8d73ae1d6) `docs(bamf): align C16.2 with bounded verification`
- [`1cf595509750`](https://github.com/Entif-AI/Bilqis-MLX/commit/1cf59550975059cb2481f9b0ecd643427ab19895) `feat(bamf): close C07.2 out-of-scope debt handling (#511)`
- [`b309146d3979`](https://github.com/Entif-AI/Bilqis-MLX/commit/b309146d3979ed4f9093f5f713d8f96ac783b4f2) `docs(bamf): remove stale cohesive witness wording`
- [`f8282c6c334b`](https://github.com/Entif-AI/Bilqis-MLX/commit/f8282c6c334b61433a0aeb36657d691bf6ce4600) `docs(bamf): turn in C16.2 flow control`
- [`66f176198af5`](https://github.com/Entif-AI/Bilqis-MLX/commit/66f176198af5ebc03fbbdc0269c36f557d65da71) `fix(bamf): use custody-backed C07 evidence paths (#511)`
- [`16fe1bc97a42`](https://github.com/Entif-AI/Bilqis-MLX/commit/16fe1bc97a428f2fd9de2b07ba486677c7f0fac1) `feat(bamf): turn in bounded learning readiness (BAMF-0.2 C16.2)`
- [`2485bd32c695`](https://github.com/Entif-AI/Bilqis-MLX/commit/2485bd32c69518730e5adc6a0360aa816529c43c) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/511-c07-out-of-scope-debt-v2-20261112`
- [`4ea79f905a53`](https://github.com/Entif-AI/Bilqis-MLX/commit/4ea79f905a53fa1b2c3d6df33c03d51d0e1d0a85) `docs(bamf): turn in C07.2 issue 511`
- [`21b95a973158`](https://github.com/Entif-AI/Bilqis-MLX/commit/21b95a97315875e91e4882d0e9343c75b3ae763e) `feat(bamf): close out-of-scope release debt handling (#511 / BAMF-0.2 C07.2)`
- [`ed544195c826`](https://github.com/Entif-AI/Bilqis-MLX/commit/ed544195c82661e127136393bf7de4d4619c043d) `feat(bamf): add event-driven C07.3 admission flywheel (#512)`
- [`9d182b849d29`](https://github.com/Entif-AI/Bilqis-MLX/commit/9d182b849d29434c08367b51c65cd90e95c32682) `fix(bamf): preserve final flywheel observation at budget (#512)`
- [`25045ab6ebfa`](https://github.com/Entif-AI/Bilqis-MLX/commit/25045ab6ebfad18c96d2ac511d26992dbaa18f5f) `fix(bamf): align flywheel with admission owner semantics (#512)`
- [`2905a58a0e83`](https://github.com/Entif-AI/Bilqis-MLX/commit/2905a58a0e83f30ed7b9450dfaf4fd73143386ed) `refactor(bamf): isolate C07 flywheel owner module (#512)`
- [`c046edace130`](https://github.com/Entif-AI/Bilqis-MLX/commit/c046edace130ac16caa569fcae15cf0307fd69df) `refactor(bamf): simplify flywheel step orchestration (#512)`
- [`f9cd80f7cb45`](https://github.com/Entif-AI/Bilqis-MLX/commit/f9cd80f7cb45767f3fb8989c04892feaf24c7220) `docs(bamf): turn in C07.3 issue 512`
- [`81273ffd8a68`](https://github.com/Entif-AI/Bilqis-MLX/commit/81273ffd8a684aa1a6a8c30a8341a043a8990271) `feat(bamf): add event-driven admission flywheel (#512 / BAMF-0.2 C07.3)`
- [`aaead5dee91a`](https://github.com/Entif-AI/Bilqis-MLX/commit/aaead5dee91ac9a9c90003981ea2187993329d6c) `BAMF-0.2 C16.3 hand off persistent student`
- [`dcb668810cb3`](https://github.com/Entif-AI/Bilqis-MLX/commit/dcb668810cb38153064b320c6fb752ac3875efbe) `Fix BAMF operator B13 admission import`
- [`bf790f7d287c`](https://github.com/Entif-AI/Bilqis-MLX/commit/bf790f7d287cd56191c581d0b0e07cc6bff8dc3f) `Use BAMF error contracts for persistent dispatch`
- [`0c33109d337e`](https://github.com/Entif-AI/Bilqis-MLX/commit/0c33109d337efab4d44c3f0f4ea0fbb73759c551) `refactor(runtime): split live autonomy owner (#1009)`
- [`ff0c6aafcd84`](https://github.com/Entif-AI/Bilqis-MLX/commit/ff0c6aafcd84de0cfa346757e9a2e9a4057cf502) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/bamf02-c-runtime`
- [`63ffa1f56e84`](https://github.com/Entif-AI/Bilqis-MLX/commit/63ffa1f56e84bd926a36d6b11798febcfa410df0) `fix(bamf): hold C16.3 on C03.4 priority authority`
- [`8c86669f87ab`](https://github.com/Entif-AI/Bilqis-MLX/commit/8c86669f87ab556491fb3f6dfc862d4944bff13b) `test(bamf): align persistent resume dispatch contract`
- [`568b9e093ae3`](https://github.com/Entif-AI/Bilqis-MLX/commit/568b9e093ae341e9d9c775d29b0deb35244ed3e9) `feat(runtime): wire accepted Atlas flywheel (#1009)`
- [`04c5915a673a`](https://github.com/Entif-AI/Bilqis-MLX/commit/04c5915a673abfd8150d2fc4339639afa25540ca) `feat(bamf): establish C03.4 production priority boundaries`
- [`cc186239958e`](https://github.com/Entif-AI/Bilqis-MLX/commit/cc186239958eaaa3de835312734f6ddbc01221c5) `fix(bamf): wire restart-safe admission flywheel into human runtime (BAMF-0.2 C07.4)`
- [`b8286f82d945`](https://github.com/Entif-AI/Bilqis-MLX/commit/b8286f82d9458bd3fbbf8aff613a9cdaf6dcd1e3) `feat(bamf): compose persistent dispatch through C03.4`
- [`153691daccd4`](https://github.com/Entif-AI/Bilqis-MLX/commit/153691daccd4c41df2ba0f884912b8e8d2e5c93a) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/bamf02-c-runtime`
- [`07e47daceeec`](https://github.com/Entif-AI/Bilqis-MLX/commit/07e47daceeec97531f0a144ae648e1ed3b066221) `fix(bamf): materialize C03.4 priority authority`
- [`ed7a7a127d3a`](https://github.com/Entif-AI/Bilqis-MLX/commit/ed7a7a127d3a3f589e4b1ef440975d826ed86d30) `fix(bamf): preserve C03.4 rejection replay`
- [`b5fd17a8f5e0`](https://github.com/Entif-AI/Bilqis-MLX/commit/b5fd17a8f5e077181af20db0e4e0547acd121500) `fix(bamf): authenticate rejection priority replay`
- [`77f27b52b305`](https://github.com/Entif-AI/Bilqis-MLX/commit/77f27b52b305495f4bc7d9dd2317232721ef87b4) `fix(bamf): bind rejection replay to B13 receipt`
- [`0b9b6d8589e7`](https://github.com/Entif-AI/Bilqis-MLX/commit/0b9b6d8589e7cea1fcd03aeac270b2488736d2a2) `refactor(bamf): split C03.4 priority owners`
- [`90e3c00e9c87`](https://github.com/Entif-AI/Bilqis-MLX/commit/90e3c00e9c871f264a07d90fc33a8772a470574f) `test(bamf): share rejection custody fixture`
- [`de91149bf844`](https://github.com/Entif-AI/Bilqis-MLX/commit/de91149bf84452564b354d995ee3744aa7ab4fdb) `docs(bamf): turn in C16.3 human handoff`
- [`c672c6211310`](https://github.com/Entif-AI/Bilqis-MLX/commit/c672c62113108695a2a60cd0eb0d7f19d085f838) `feat(bamf): handoff persistent BAMF through C03.4 (BAMF-0.2 C16.3)`
- [`dd577800011c`](https://github.com/Entif-AI/Bilqis-MLX/commit/dd577800011c478f1610739e20e533dd5449ff81) `docs(bamf): reconcile C11.3 operator runbook (#524)`
- [`cdf065c91820`](https://github.com/Entif-AI/Bilqis-MLX/commit/cdf065c91820df8b46f39269f6a239122027a833) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/524-c11-closure-20261112`
- [`ec2843ebaf78`](https://github.com/Entif-AI/Bilqis-MLX/commit/ec2843ebaf78f08d668225284c1ed8b64d96581b) `fix(bamf): continue leased resume into operator (#524)`
- [`a1b83786536e`](https://github.com/Entif-AI/Bilqis-MLX/commit/a1b83786536eaa3fea51f7332431c456298f625d) `test(bamf): prove teacher-selected acquisition (#1004)`
- [`d8b7cf96774e`](https://github.com/Entif-AI/Bilqis-MLX/commit/d8b7cf96774e4d072d9ac7281cd741dd8c9ca7f5) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/bamf02-b-neural`
- [`be9af6f74445`](https://github.com/Entif-AI/Bilqis-MLX/commit/be9af6f7444588fe3cbe3e62da501e1214d7e5bd) `test(bamf): isolate C05 genesis trust identity (#1004)`
- [`03a249714a2b`](https://github.com/Entif-AI/Bilqis-MLX/commit/03a249714a2b861848817cc4bb0251cbe01008a4) `docs(bamf): requalify C01 dependency holds`
- [`ff302ab3dc29`](https://github.com/Entif-AI/Bilqis-MLX/commit/ff302ab3dc29115f89da6fa97b0779cef001780f) `test(bamf): prove human restart-safe C07 composition (#1012)`
- [`fe01c6a3687d`](https://github.com/Entif-AI/Bilqis-MLX/commit/fe01c6a3687d836abd3b0d4c13df392539ae1f95) `test(c10): pin factory adoption projection boundary`
- [`907f5a3bff33`](https://github.com/Entif-AI/Bilqis-MLX/commit/907f5a3bff339390db949cd82efcb40691acfa85) `feat(bamf): reconcile persistent launch and leased resume (#524 / BAMF-0.2 C11.3)`
- [`cef1cfd32140`](https://github.com/Entif-AI/Bilqis-MLX/commit/cef1cfd32140158ea13578fa45b5a359cf83df40) `fix(bamf): requalify dependency holds without manufacturing readiness (BAMF-0.2 C01)`
- [`4688fd927053`](https://github.com/Entif-AI/Bilqis-MLX/commit/4688fd9270532e92f023b9b1424ccb8cfc53f6cf) `fix(bamf): prove restart-safe C07 production composition (BAMF-0.2 C07.5)`
- [`e3b8f743752c`](https://github.com/Entif-AI/Bilqis-MLX/commit/e3b8f743752c5af7e1e8fea4cbe834dc4c40eacd) `feat(bamf): pin current C07 adoption projection boundary (BAMF-0.2 C10.1)`
- [`e4e6baf54529`](https://github.com/Entif-AI/Bilqis-MLX/commit/e4e6baf54529e50b64af217ff4666260cd4ef634) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/bamf02-b-neural`
- [`c463db04b71c`](https://github.com/Entif-AI/Bilqis-MLX/commit/c463db04b71c26e1c77666daf91c5fdc033f3a41) `test(bamf): bind accepted C05 proof to teacher acquisition (#1004)`
- [`48f7b2f8ecdc`](https://github.com/Entif-AI/Bilqis-MLX/commit/48f7b2f8ecdc911f698222c4e45a282f05ad7ad0) `test(bamf): prepare C13 disposable learning fixtures (#528)`
- [`bb389d9808ff`](https://github.com/Entif-AI/Bilqis-MLX/commit/bb389d9808ff7c14c6c6ba14da5363636abb1c9f) `fix(bamf): make C13 fixture TaskGoal executable (#528)`
- [`74adb5892e8d`](https://github.com/Entif-AI/Bilqis-MLX/commit/74adb5892e8dc53dd910c9a0455fa79dab93943d) `test(bamf): publish disposable C13 foundation (#528)`
- [`7ca2725833aa`](https://github.com/Entif-AI/Bilqis-MLX/commit/7ca2725833aac6ef567307184e1b9bc2d337b198) `feat(c10): project accepted BAMF owner custody`
- [`2cba80bb3b93`](https://github.com/Entif-AI/Bilqis-MLX/commit/2cba80bb3b9315e22af349e9336418e798200da8) `test(bamf): bound C13 owner candidate attempts (#528)`
- [`14b78acdb549`](https://github.com/Entif-AI/Bilqis-MLX/commit/14b78acdb549205869288124657cf3f486f8c8a2) `fix(c10): scope unknown time to owner projections`
- [`73e8b2ebb224`](https://github.com/Entif-AI/Bilqis-MLX/commit/73e8b2ebb2246d8c899d0a150513078022c25c4e) `test(bamf): compile disposable C13 episode source (#528)`
- [`26f284f42eeb`](https://github.com/Entif-AI/Bilqis-MLX/commit/26f284f42eeb6b8effa58eb9168476e8eaa37acc) `test(bamf): bind C13 cold restart identity (#528)`
- [`2aeb634860ac`](https://github.com/Entif-AI/Bilqis-MLX/commit/2aeb634860ac5d44726f06de29df0bf7c49e0190) `fix(c10): require owner authority for production projections`
- [`d0b692648914`](https://github.com/Entif-AI/Bilqis-MLX/commit/d0b6926489149d53c8af4361059f6f35e4896052) `fix(c10): close production owner authority seams`
- [`ce1f91d19896`](https://github.com/Entif-AI/Bilqis-MLX/commit/ce1f91d19896444788ad6e0bc8eabe32d62b2a93) `refactor(c10): split owner projection adapters`
- [`b40c26b28436`](https://github.com/Entif-AI/Bilqis-MLX/commit/b40c26b2843691212b460e49602b0a02b2cdedae) `feat(bamf): prove teacher-selected assembled-model acquisition (BAMF-0.2 #1004)`
- [`009263acb786`](https://github.com/Entif-AI/Bilqis-MLX/commit/009263acb78662f9933469ebf9f666722c1c7679) `feat(bamf): project accepted BAMF owner custody (BAMF-0.2 C10.1)`
- [`ea9370290687`](https://github.com/Entif-AI/Bilqis-MLX/commit/ea93702906872801afdb68927e9f8c08737b705c) `test(bamf): validate C13 semantic delta composition (#528)`
- [`58adf3ffab01`](https://github.com/Entif-AI/Bilqis-MLX/commit/58adf3ffab01a86ea670a27e695d8fe0da561504) `test(bamf): bind C13 semantic delta receipt (#528)`
- [`1150f7d8ca65`](https://github.com/Entif-AI/Bilqis-MLX/commit/1150f7d8ca65b564906150c266c3b261ccb3b030) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/528-c13-fixtures-20261112`
- [`ea4828e7485f`](https://github.com/Entif-AI/Bilqis-MLX/commit/ea4828e7485f3afcbd12ee65cd8d6fafe34f0512) `fix(bamf): normalize B13.6 dependency receipts`
- [`8a67920c2ced`](https://github.com/Entif-AI/Bilqis-MLX/commit/8a67920c2cedcbb0c42e0298782cb697ed5df426) `fix(bamf): normalize A03.4 serialization receipt`
- [`9849c31c08e3`](https://github.com/Entif-AI/Bilqis-MLX/commit/9849c31c08e3ee0ba89ab7fad259362bcbdb6316) `fix(bamf): normalize A05.4 compiler receipt`
- [`b102db013ff9`](https://github.com/Entif-AI/Bilqis-MLX/commit/b102db013ff9ddc29c9fcf078f3efa6f6539fce2) `fix(bamf): normalize A08.1b.2 A13.1 receipt`
- [`c4b912d76b6b`](https://github.com/Entif-AI/Bilqis-MLX/commit/c4b912d76b6b8122458ace2f5c1885a31b60b2b1) `fix(bamf): normalize B02.4 compiled-handle receipt`
- [`27e68412d5f0`](https://github.com/Entif-AI/Bilqis-MLX/commit/27e68412d5f007d1f84a05e7af81753fb0b15da0) `fix(bamf): normalize B11.1a cycle receipts`
- [`17ecbdfdb636`](https://github.com/Entif-AI/Bilqis-MLX/commit/17ecbdfdb636a78a17ac6a68fa601082370916e8) `fix(bamf): harden B11 amendment provenance`
- [`e3e2593cd3fc`](https://github.com/Entif-AI/Bilqis-MLX/commit/e3e2593cd3fc49f43998b65ecb3ab3f327fd77a3) `test(bamf): split C01 dependency normalization coverage`
- [`192ac9c483ac`](https://github.com/Entif-AI/Bilqis-MLX/commit/192ac9c483ac69ac5e696f3796baafa4d788e2e4) `test(bamf): satisfy dependency test hygiene gate`
- [`bd5ed2861035`](https://github.com/Entif-AI/Bilqis-MLX/commit/bd5ed28610351d37907671c6002d2fc8d20d5124) `fix(bamf): normalize six C01 dependency holds`
- [`6a2c44d1ecb0`](https://github.com/Entif-AI/Bilqis-MLX/commit/6a2c44d1ecb0f1ff725ba90396c5844ad7d0ae99) `fix(bamf): resolve final C01 dependency holds`
- [`42c7c3093c3a`](https://github.com/Entif-AI/Bilqis-MLX/commit/42c7c3093c3a20f04e0a2d3b74777c8ee17e4767) `fix(bamf): preserve final receipt roles`
- [`38a540b88658`](https://github.com/Entif-AI/Bilqis-MLX/commit/38a540b88658985569acff8aca7716686fc5a281) `fix(bamf): make final authority parsers terminal`
- [`ce09a0c18870`](https://github.com/Entif-AI/Bilqis-MLX/commit/ce09a0c1887069385b903ac10a4d576d22d04881) `fix(bamf): preserve A02 successor semantic custody (#524)`
- [`554af14fe2e5`](https://github.com/Entif-AI/Bilqis-MLX/commit/554af14fe2e5e0f5b78ac07d9b067c4a5a96678d) `fix(bamf): resolve final C01 dependency holds`
- [`0ae919779e1d`](https://github.com/Entif-AI/Bilqis-MLX/commit/0ae919779e1de44f5c7c96e911b3f61780099e21) `feat(bamf): preserve successor semantic custody on leased resume (#524 / BAMF-0.2 C11.3)`
- [`0d7af6c6afb0`](https://github.com/Entif-AI/Bilqis-MLX/commit/0d7af6c6afb08b2dd7deb6b24f8c303487623b28) `feat(bamf): admit C13 episode source authority`
- [`6eb2b863035a`](https://github.com/Entif-AI/Bilqis-MLX/commit/6eb2b863035ad925b5406de8e662524b23e12975) `fix(bamf): close final C01 EGM findings`
- [`5871873117ad`](https://github.com/Entif-AI/Bilqis-MLX/commit/5871873117ad8d239bace87064a4221f275f152b) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/347-c01-final-authority-20261112`
- [`c54dea6d9a70`](https://github.com/Entif-AI/Bilqis-MLX/commit/c54dea6d9a708c924179b93351f4818ab9c30acf) `docs(bamf): reconcile C01 post-merge provenance`
- [`a74011bab1f7`](https://github.com/Entif-AI/Bilqis-MLX/commit/a74011bab1f70248c4cf146af441c974fb02e4b4) `fix(bamf): govern C13 source errors`
- [`99a903da16b1`](https://github.com/Entif-AI/Bilqis-MLX/commit/99a903da16b1d2ddc5be6cc145e77e629c88fc01) `test(bamf): exercise exact receipt source binding`
- [`9b44594cf117`](https://github.com/Entif-AI/Bilqis-MLX/commit/9b44594cf11721e9e08a3f01d36108a7eae6d532) `feat(bamf): admit C13 episode source authority (BAMF-0.2 #1020)`
- [`6e74cb3f33b3`](https://github.com/Entif-AI/Bilqis-MLX/commit/6e74cb3f33b3e823b9133e2675f031854a85fd0a) `docs(bamf): pin C01 merged candidate lineage`
- [`93fd88b9e1fc`](https://github.com/Entif-AI/Bilqis-MLX/commit/93fd88b9e1fc7245ba13bae1c6b1999d702dd194) `docs(bamf): record final C01 EGM pass`
- [`efb6d7aa3b35`](https://github.com/Entif-AI/Bilqis-MLX/commit/efb6d7aa3b35d8bf4d595139efa58ea7c638e54e) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/347-c01-final-authority-20261112`
- [`97a018ed7e96`](https://github.com/Entif-AI/Bilqis-MLX/commit/97a018ed7e9697fe284abd9fa8197cd7f4194b45) `fix(bamf): close final C01 EGM findings`
- [`9853d5b14654`](https://github.com/Entif-AI/Bilqis-MLX/commit/9853d5b1465418b2dbe4a6d3e1d98e44f22f61da) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/528-c13-fixtures-20261112`
- [`19c3faaa7b5d`](https://github.com/Entif-AI/Bilqis-MLX/commit/19c3faaa7b5da6d9199976e4bcfc9db4e34dba6c) `feat(bamf): declare C14 developmental program (#532)`
- [`77006d2370a1`](https://github.com/Entif-AI/Bilqis-MLX/commit/77006d2370a16e0bfb4ca1a10cc516a6e4d011f8) `fix(bamf): harden C14 program manifest (#532)`
- [`4759336facf7`](https://github.com/Entif-AI/Bilqis-MLX/commit/4759336facf7a3482254b32c8647013ae447f074) `feat(bamf): establish C15 delivery receipt boundary`
- [`71b690da860f`](https://github.com/Entif-AI/Bilqis-MLX/commit/71b690da860f4595720d594e5bfcf516a0e10a44) `feat(bamf): resolve C14 developmental stage intent (#533)`
- [`030aa51d5e3f`](https://github.com/Entif-AI/Bilqis-MLX/commit/030aa51d5e3f1e669648831cee2b7b340dab1c67) `feat(bamf): publish C15 delivery projection`
- [`549d84d5cb58`](https://github.com/Entif-AI/Bilqis-MLX/commit/549d84d5cb58862c92eca2dd25277d5ca0665fd7) `feat(c13): wire disposable integrated learning witness`
- [`bd44dbfca9d2`](https://github.com/Entif-AI/Bilqis-MLX/commit/bd44dbfca9d27412a578abb76181a8bcd9bafeba) `fix(bamf): enforce C14 interleaving policy (#533)`
- [`618c1d45a509`](https://github.com/Entif-AI/Bilqis-MLX/commit/618c1d45a509dbf75781ab15cff7b720343bb9b9) `docs(bamf): add C14 training runbook (#534)`
- [`39c25883fc72`](https://github.com/Entif-AI/Bilqis-MLX/commit/39c25883fc72dcd4751c242ae99cf5ae08d4cd38) `chore(bamf): reconcile C14 review state (#534)`
- [`96ec126f0a9a`](https://github.com/Entif-AI/Bilqis-MLX/commit/96ec126f0a9a02d9e1adaafcdd5dbf859d6d1111) `feat(bamf): enforce C15 evidence admission`
- [`4ea379354993`](https://github.com/Entif-AI/Bilqis-MLX/commit/4ea3793549932aa55592bf437202b4f95d0418c8) `feat(bamf): codify recursive C14 domain succession (#535)`
- [`da6857edf454`](https://github.com/Entif-AI/Bilqis-MLX/commit/da6857edf454d6273565705139c2adf75fc0d4d1) `chore(bamf): record C14 domain-rule receipt (#535)`
- [`014c6b23fc64`](https://github.com/Entif-AI/Bilqis-MLX/commit/014c6b23fc640ba357b6ec64c3703a5c5f386a99) `fix(bamf): enforce C14 domain contracts (#535)`
- [`415d143fa848`](https://github.com/Entif-AI/Bilqis-MLX/commit/415d143fa848c5662fa7e007117a1e403686c224) `chore(bamf): record C14 domain-contract repair (#535)`
- [`9eb06abe3218`](https://github.com/Entif-AI/Bilqis-MLX/commit/9eb06abe3218d7d4853442d2b0550331c0f49980) `fix(bamf): bind C14 rule authority (#535)`
- [`17baa8ef557b`](https://github.com/Entif-AI/Bilqis-MLX/commit/17baa8ef557b3d091083e7d553b31ee6f8392fc9) `chore(bamf): record final C14 rule-authority repair (#535)`
- [`e560ccbf6a62`](https://github.com/Entif-AI/Bilqis-MLX/commit/e560ccbf6a62480ee0f079e8343b43c5583bc1ab) `fix(c13): run cold restart from repository root`
- [`b4e56d6a2954`](https://github.com/Entif-AI/Bilqis-MLX/commit/b4e56d6a2954e0c06f01bca9d121471cbfe181c0) `test(bamf): clean C14 domain-rule witness (#535)`
- [`1a4d0675b148`](https://github.com/Entif-AI/Bilqis-MLX/commit/1a4d0675b148c988cd3d916490526ae362b5304e) `chore(bamf): record clean C14 rule witness (#535)`
- [`a008e1d2770c`](https://github.com/Entif-AI/Bilqis-MLX/commit/a008e1d2770c968e1b7784d00194e4f75e402041) `fix(bamf): harden C15 evidence closure`
- [`eb09d0690d16`](https://github.com/Entif-AI/Bilqis-MLX/commit/eb09d0690d162266e22f8a3b2052bb10a628c9f0) `docs(bamf): align C15 EGM repair receipts`
- [`732f85af3ecc`](https://github.com/Entif-AI/Bilqis-MLX/commit/732f85af3ecc1b2fc6ea2ce6cb68b4f91c2fed28) `feat(c13): prepare rollback and correction qualification`
- [`13e43695f1e8`](https://github.com/Entif-AI/Bilqis-MLX/commit/13e43695f1e8a8d8a14c0f872d2e397f957ccea3) `fix(bamf): bind C15 pass admission to repo authority`
- [`4da6cfbbe1f3`](https://github.com/Entif-AI/Bilqis-MLX/commit/4da6cfbbe1f326021f75fa475df416159b325711) `fix(bamf): bind execution receipts to commit trees`
- [`66277ed61d0a`](https://github.com/Entif-AI/Bilqis-MLX/commit/66277ed61d0ae4cabb088dfb508ab7188415003c) `fix(bamf): separate C15 candidate and attestation commits`
- [`dc89862628e0`](https://github.com/Entif-AI/Bilqis-MLX/commit/dc89862628e0e7d3c74606715217d5394301b1ea) `docs(bamf): attest C15 reviewed snapshot identity`
- [`fc04b9379e56`](https://github.com/Entif-AI/Bilqis-MLX/commit/fc04b9379e5657cd046836c4af9ea4dd76df4795) `docs(bamf): record C15 EGM closeout`
- [`235182590eae`](https://github.com/Entif-AI/Bilqis-MLX/commit/235182590eaefa6813bf3fae9f679099dc02ed75) `docs(bamf): publish C15 EGM pass receipts`
- [`6ca32b415e88`](https://github.com/Entif-AI/Bilqis-MLX/commit/6ca32b415e8861856bdd8f4aa584247f7ad3a3e4) `fix(bamf): separate live hierarchy from dependency DAG`
- [`9dac7223b8dc`](https://github.com/Entif-AI/Bilqis-MLX/commit/9dac7223b8dc03ff56470f2a8ce72bc01151ca25) `docs(bamf): reconcile C15 live issue authority`
- [`3b5e920ff074`](https://github.com/Entif-AI/Bilqis-MLX/commit/3b5e920ff074f0ebd0908edd739c16fb98fc8eac) `docs(bamf): record C15.3 live reconciliation`
- [`95e0bf310c0a`](https://github.com/Entif-AI/Bilqis-MLX/commit/95e0bf310c0a723ebaf8771eda8e45f5919ef2fc) `docs(bamf): pin C15.3 active architecture snapshot`
- [`ada12418a975`](https://github.com/Entif-AI/Bilqis-MLX/commit/ada12418a975443afa5ff9fe13963e5d0fc14648) `refactor(mainline): replace legacy tree with reviewed BAMF trunk`
- [`39bafa233c60`](https://github.com/Entif-AI/Bilqis-MLX/commit/39bafa233c6070330ee69ef4fc59d70efe0008a6) `chore(mainline): join reviewed BAMF unified history`
- [`e3d8e585c84d`](https://github.com/Entif-AI/Bilqis-MLX/commit/e3d8e585c84d49994575976b16e1e3fafdc1626b) `refactor(mainline): preserve release control on BAMF bridge`
- [`8fd258a625f4`](https://github.com/Entif-AI/Bilqis-MLX/commit/8fd258a625f4d7d8c10fd08521594fc0f27960f5) `fix(bamf): bound live issue newline transport`
- [`4212d278ee1b`](https://github.com/Entif-AI/Bilqis-MLX/commit/4212d278ee1b97d87ea6855172ca76fb2b1e6562) `docs(bamf): audit post-registry native hierarchy`
- [`16117bfb782c`](https://github.com/Entif-AI/Bilqis-MLX/commit/16117bfb782ce0b1a3f301e2f5441917a915fd9d) `docs(bamf): record executed C15.3 factory witnesses`
- [`2ffdfda3a1cc`](https://github.com/Entif-AI/Bilqis-MLX/commit/2ffdfda3a1cc0e02ddc5cb499f23990c3000a9b6) `ci(mainline): validate bridge against unified baseline`
- [`07cdf41380a6`](https://github.com/Entif-AI/Bilqis-MLX/commit/07cdf41380a6f325f72de9d3b64e7451f74fcca7) `fix(bamf): reserve C13 source binding namespace (#1032)`
- [`51e85f12d407`](https://github.com/Entif-AI/Bilqis-MLX/commit/51e85f12d407d0dfbfddf1cca8774c3219d22747) `docs(bamf): freeze unprivileged C09 authority design (#1031)`
- [`d53b4381c4c9`](https://github.com/Entif-AI/Bilqis-MLX/commit/d53b4381c4c9ec7ef43d6021361f1726c0bfa22e) `test(bamf): exercise C13 reservation through compiler (#1032)`
- [`42c17e54bc2e`](https://github.com/Entif-AI/Bilqis-MLX/commit/42c17e54bc2e9e2bcea2d82cfe545221498ba62d) `feat(bamf): enforce C13 source binding reservation (BAMF-0.2 #1030b)`
- [`39029d930ee1`](https://github.com/Entif-AI/Bilqis-MLX/commit/39029d930ee14af5ed51add42e35e8e60c929550) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/1031-unprivileged-trust-root-20261113`
- [`bc283e9480b4`](https://github.com/Entif-AI/Bilqis-MLX/commit/bc283e9480b4dd60957ef5eaafe86dc7bff08496) `fix(bamf): move C09 authority to ordinary-user store (#1031)`
- [`05a32baa0c3c`](https://github.com/Entif-AI/Bilqis-MLX/commit/05a32baa0c3ced5e986c7de74b1403c1225dc43d) `feat(bamf): move C09 authority to fixed ordinary-user store (BAMF-0.2 #1031)`
- [`fbb2e155f1cc`](https://github.com/Entif-AI/Bilqis-MLX/commit/fbb2e155f1cc1b26a6a96d3ea2f266a74347eaea) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/528-c13-fixtures-20261112`
- [`47e57f05574b`](https://github.com/Entif-AI/Bilqis-MLX/commit/47e57f05574b7702a85772003c5fc892ff206a33) `feat(bamf): turn in integrated M3 Ultra wiring path (BAMF-0.2 C13.1)`
- [`7dc5711aee26`](https://github.com/Entif-AI/Bilqis-MLX/commit/7dc5711aee26a2d2050153384622e2da4574711f) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/529-c13-rollback-20261113`
- [`f5ddda6cf5db`](https://github.com/Entif-AI/Bilqis-MLX/commit/f5ddda6cf5db68267678b7fcd4a3f5f143e4f1b4) `docs(bamf): prepare C13 integration handoff (#530)`
- [`b99810cbf69b`](https://github.com/Entif-AI/Bilqis-MLX/commit/b99810cbf69bf6a379e00056fdec9845dca1245d) `feat(bamf): reconcile rollback, resume and correction proofs (BAMF-0.2 C13.2)`
- [`fcbe0cc06d66`](https://github.com/Entif-AI/Bilqis-MLX/commit/fcbe0cc06d66648b0bd745516b9ba7cb26170529) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/530-c13-handoff-20261113`
- [`4b486268825f`](https://github.com/Entif-AI/Bilqis-MLX/commit/4b486268825f07330c4bd8147ca2439a36be5fee) `docs(bamf): finalize C13 integration handoff (#530)`
- [`9e06ea557c91`](https://github.com/Entif-AI/Bilqis-MLX/commit/9e06ea557c910bae7ecd879fe83f4d50aed84eb9) `feat(bamf): publish integrated wiring receipt and dashboard handoff (BAMF-0.2 C13.3)`
- [`7ec38cbee880`](https://github.com/Entif-AI/Bilqis-MLX/commit/7ec38cbee8807397700d3cad0123341be0b8aeb6) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/532-c14-program-20261113`
- [`98dc353007be`](https://github.com/Entif-AI/Bilqis-MLX/commit/98dc353007bebaece162d81e1797895c3d353c84) `Merge remote-tracking branch 'origin/codex/532-c14-program-20261113' into codex/533-c14-stage-20261113`
- [`4ca647238e26`](https://github.com/Entif-AI/Bilqis-MLX/commit/4ca647238e26a302ee1fc6446cd772471e31115f) `Merge remote-tracking branch 'origin/codex/533-c14-stage-20261113' into codex/534-c14-runbook-20261113`
- [`29101af83aaa`](https://github.com/Entif-AI/Bilqis-MLX/commit/29101af83aaa592ab1ace59c68bfdba153c7fb53) `Merge remote-tracking branch 'origin/codex/534-c14-runbook-20261113' into codex/535-c14-domain-rules-20261113`
- [`f690edca471f`](https://github.com/Entif-AI/Bilqis-MLX/commit/f690edca471fb40101b563353bdb0c257d7bba32) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/bamf02-c-runtime`
- [`8a8c9744c5c1`](https://github.com/Entif-AI/Bilqis-MLX/commit/8a8c9744c5c10f8290f1e717b0adc1cbc5ccf191) `feat(bamf): declare developmental program (BAMF-0.2 C14.1a)`
- [`6719eb506bd2`](https://github.com/Entif-AI/Bilqis-MLX/commit/6719eb506bd2b8f2fc2ba92b9113f9b734395295) `feat(bamf): select lawful interleaved stages (BAMF-0.2 C14.1b)`
- [`7550492c63eb`](https://github.com/Entif-AI/Bilqis-MLX/commit/7550492c63eba163daf7d5a0397ab7896cee349b) `feat(bamf): deliver source-coverage training runbook (BAMF-0.2 C14.2)`
- [`d81c1ae5ab95`](https://github.com/Entif-AI/Bilqis-MLX/commit/d81c1ae5ab951bfbefb5d72e9dc04f9f746bc9b1) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/535-c14-domain-rules-20261113`
- [`a72192b0b0cb`](https://github.com/Entif-AI/Bilqis-MLX/commit/a72192b0b0cb0fa5aade1f87dd2677603cbcee51) `fix(bamf): reconcile C13 release boundary for C15`
- [`68a48312ad21`](https://github.com/Entif-AI/Bilqis-MLX/commit/68a48312ad21e5ae137dbebc7cdd3b3871c8843d) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/bamf02-c-runtime`
- [`c3649b501053`](https://github.com/Entif-AI/Bilqis-MLX/commit/c3649b50105325847730e15148966f8369c73342) `feat(bamf): consume C15 requalification receipts`
- [`ed9b5e00c699`](https://github.com/Entif-AI/Bilqis-MLX/commit/ed9b5e00c699eb30b7519b448bf76563693b4206) `refactor(bamf): keep C15 requalification runner bounded`
- [`de84266ba3db`](https://github.com/Entif-AI/Bilqis-MLX/commit/de84266ba3db79b6545ff484f3268a99ea8872f6) `feat(bamf): recursive grade-neutral domain succession (BAMF-0.2 C14.3)`
- [`16cdbd24c385`](https://github.com/Entif-AI/Bilqis-MLX/commit/16cdbd24c3856f172fd4b4f109bcb2612c607fa7) `Merge remote-tracking branch 'origin/codex/bamf-unified-base-20261028' into codex/bamf02-c-runtime`
- [`e84503682d49`](https://github.com/Entif-AI/Bilqis-MLX/commit/e84503682d494f19dece9f531aa4e94e40a4e9a3) `feat(bamf): consume accepted C14 for C15 closeout`
- [`c4197f28c4aa`](https://github.com/Entif-AI/Bilqis-MLX/commit/c4197f28c4aa2e3972634b1dbea255832d4b6d7b) `fix(bamf): bind C15 proof to executable owner tests`
- [`f2189cce5d49`](https://github.com/Entif-AI/Bilqis-MLX/commit/f2189cce5d49b1c97dcf1ff67b70b0925322b663) `test(bamf): attest final C15 conformance receipts`
- [`e8262d01093f`](https://github.com/Entif-AI/Bilqis-MLX/commit/e8262d01093fa5ee77991a482d60c8b99585d9e2) `feat(bamf): publish C15 ready-for-owner-merge state`
- [`7af2566a5751`](https://github.com/Entif-AI/Bilqis-MLX/commit/7af2566a57516d13eea8f6ede37b23d5b259e212) `refactor(bamf): split C15 publication projection`
- [`057638a2c93c`](https://github.com/Entif-AI/Bilqis-MLX/commit/057638a2c93cd152516457c6a5b0b92a946454c1) `feat(bamf): close delivery with immutable conformance receipts (BAMF-0.2 C15)`
- [`c45a84810e35`](https://github.com/Entif-AI/Bilqis-MLX/commit/c45a84810e35ba6f189a8c60eaf79366c69a49f4) `ci(bamf): merge unified base to bridge`
- [`381386adb2a7`](https://github.com/Entif-AI/Bilqis-MLX/commit/381386adb2a7c6183276430672a5744b92124301) `ci(bamf): merge BAMF-0.2 bridge cutover to main`
- [`21a84dba60b1`](https://github.com/Entif-AI/Bilqis-MLX/commit/21a84dba60b19027ae77fdfe4b722ff860a2f3f8) `chore(gitignore): nobody likes being ignored`

## [1.0.0](https://github.com/Entif-AI/Bilqis-MLX/compare/v0.2.0...v1.0.0) (2026-11-13)


### ⚠ BREAKING CHANGES

* **skos:** importer CLI 2.0.0 requires an explicit pinned smoke suite and emits a validated materialization receipt.

### Features

* **bill-keys:** worked til I could not anymore ([599deb1](https://github.com/Entif-AI/Bilqis-MLX/commit/599deb13257d7400c792d481bc27bc7b304ccb14))
* **championship:** defend capability titles head to head ([e75ebb7](https://github.com/Entif-AI/Bilqis-MLX/commit/e75ebb7240b6253229142050d28eefba026a607c))
* **champions:** improved examination and promotion of balboa-types ([1d78ccc](https://github.com/Entif-AI/Bilqis-MLX/commit/1d78cccd2753e9259c1646a873bd54e28948cff1))
* **curriculum:** add reduced boolean grade profile ([16f0a67](https://github.com/Entif-AI/Bilqis-MLX/commit/16f0a671f6db0c2397a23f9313541cebc6c6654d))
* **curriculum:** factory for metalearning new curriculum segments ([3d0a271](https://github.com/Entif-AI/Bilqis-MLX/commit/3d0a2710a5749ead1922a9cbb40cb9ece4663df1))
* **curriculum:** factory for metalearning new curriculum segments ([ef33423](https://github.com/Entif-AI/Bilqis-MLX/commit/ef33423dd99e7146025a7322b78b24b0372285cc))
* **curriculum:** factory for metalearning new curriculum segments ([c76fb0d](https://github.com/Entif-AI/Bilqis-MLX/commit/c76fb0d2cd120f09da20c10adcbc4f0b0136f513))
* **curriculum:** landmark AND and IMPLIES operands ([8fc431c](https://github.com/Entif-AI/Bilqis-MLX/commit/8fc431cfbc254ad9bdf81ed03f661f51250113e5))
* **curriculum:** landmark composite proof roles ([c3686e7](https://github.com/Entif-AI/Bilqis-MLX/commit/c3686e728bdfef1086bb5c895952a0d5cb31b7a9))
* **curriculum:** preserve thin profiles through debt admission ([3b98b0d](https://github.com/Entif-AI/Bilqis-MLX/commit/3b98b0d3fb12b067ada0c3d6272e5fe08890e826))
* **curriculum:** promote stable grade means ([dd4dd9d](https://github.com/Entif-AI/Bilqis-MLX/commit/dd4dd9d6a47bb22dd5755864451cb13156a09aff))
* **curriculum:** raise numeric root ceiling to six ([b4397c4](https://github.com/Entif-AI/Bilqis-MLX/commit/b4397c46293e8328787a1d4a5b96dee6ee49d73c))
* **curriculum:** restore IDBOOLOPS binding landmarks ([2ec0150](https://github.com/Entif-AI/Bilqis-MLX/commit/2ec0150f1b193ed243c3f3ead7634a11f8e0caaa))
* **curriculum:** teach and assess contrasting event queries ([9c25cea](https://github.com/Entif-AI/Bilqis-MLX/commit/9c25cea0b955ca48c04884e98079de0ce92c733d))
* **curriculum:** trial smaller event slices through source-owned lessons ([71e2ca0](https://github.com/Entif-AI/Bilqis-MLX/commit/71e2ca0223418546e5adae6560a5a40084f492f0))
* **dashboard:** add retention percentage ([0fa95da](https://github.com/Entif-AI/Bilqis-MLX/commit/0fa95da554bf1135f219dafba8b499a18c99b751))
* **dashboard:** add retentions per hour ([41c8b6c](https://github.com/Entif-AI/Bilqis-MLX/commit/41c8b6c3eab63229617840e7e7900ef6c484a2fa))
* **dashboard:** add whole-school growth average ([728f91a](https://github.com/Entif-AI/Bilqis-MLX/commit/728f91ab8ad63f50eb153e0bdd11f7528bdbf418))
* **dashboard:** align growth and compact system state ([8d10416](https://github.com/Entif-AI/Bilqis-MLX/commit/8d10416d1e0f3f966c2ea22a8d2621d43ad5433e))
* **dashboard:** collapse header to cockpit summary ([20c638c](https://github.com/Entif-AI/Bilqis-MLX/commit/20c638cf1d7cb3377dcbfc4c16e241d4df4a0f8a))
* **dashboard:** compact middle telemetry pane ([162e176](https://github.com/Entif-AI/Bilqis-MLX/commit/162e1765109d5d71a77cab321a841a253b80be4f))
* **dashboard:** compact telemetry columns ([2337fc6](https://github.com/Entif-AI/Bilqis-MLX/commit/2337fc615cfb4ca11dd3b05cb42b4e1f04e54d25))
* **dashboard:** compaction initiated... please stand by for catastrophic forgetting ([7fef150](https://github.com/Entif-AI/Bilqis-MLX/commit/7fef150afeb36249ec93f717d20f396ce465fad8))
* **dashboard:** fold family telemetry into mastery ([81a8369](https://github.com/Entif-AI/Bilqis-MLX/commit/81a83690e854c61911857cc91b4dbd5941f3820e))
* **dashboard:** move curriculum coordinates to cockpit ([f092c1c](https://github.com/Entif-AI/Bilqis-MLX/commit/f092c1c986274f8d1bb9b06829d2471571c2974c))
* **dashboard:** move train score into mastery header ([6ebbe92](https://github.com/Entif-AI/Bilqis-MLX/commit/6ebbe92933c9febb1406d18b896b4295449362fb))
* **dashboard:** render cockpit as two-row header ([18f7bc0](https://github.com/Entif-AI/Bilqis-MLX/commit/18f7bc0b4213e4f066193677f17254b2261a62db))
* **dashboard:** show capability and champion rows ([5ce1a00](https://github.com/Entif-AI/Bilqis-MLX/commit/5ce1a006880fe1dc02c6fa6577d0859494a8ee72))
* **dashboard:** surface numeric scope milestones ([c0a8a4c](https://github.com/Entif-AI/Bilqis-MLX/commit/c0a8a4c58d901874dc45505b66295bbc197f37ac))
* **dashboard:** you like-a my dashboard, doncha baby ([8a85601](https://github.com/Entif-AI/Bilqis-MLX/commit/8a856019f79c7882bd71d75e09c82ef15116a66f))
* **diagnostics:** generate deterministic learning history report ([ed438f4](https://github.com/Entif-AI/Bilqis-MLX/commit/ed438f4bfbe45826d1bd44dd322dab7c244fbe77))
* **experiment:** add Ithkuil source graph and enrichment ([d59e77e](https://github.com/Entif-AI/Bilqis-MLX/commit/d59e77ec0a5f9747e57c023ef5aee06abb38d818))
* **experiment:** build relational Ithkuil grammar dataset ([8651863](https://github.com/Entif-AI/Bilqis-MLX/commit/865186371953f871cb1871cd56401c1f317af7ed))
* **experiments:** retain reproducible query-binding trial evidence ([d785ffc](https://github.com/Entif-AI/Bilqis-MLX/commit/d785ffc54f82a3f6ea01790e20c16f5e8a89bf63))
* **factory:** add exact-scope assessment lifecycle ([3bfe758](https://github.com/Entif-AI/Bilqis-MLX/commit/3bfe7584fb53ad1d1905383b13bc7f2c19231b78))
* **factory:** add executable release admission v2 ([5a73db5](https://github.com/Entif-AI/Bilqis-MLX/commit/5a73db549e04f2a4f0d0c1b66be3326fa2eaa937))
* **factory:** add live answer modality registry ([49e203f](https://github.com/Entif-AI/Bilqis-MLX/commit/49e203ffb21995e9687adbe66d98ec13c827fc38))
* **factory:** add progressive understanding proof projections ([3cc251b](https://github.com/Entif-AI/Bilqis-MLX/commit/3cc251bf5df93b091adcd4187ed51c99974807d1))
* **factory:** add receipt-backed autonomous evidence planner ([6fe72b7](https://github.com/Entif-AI/Bilqis-MLX/commit/6fe72b7ba0b024281d3bb60ca80988b9b95d1d28))
* **factory:** admit executable release in trainer ([a9d6897](https://github.com/Entif-AI/Bilqis-MLX/commit/a9d6897d043590f457c6eac3aa6d46666e5e85f9))
* **factory:** adopt appended profiles generically ([2391a8a](https://github.com/Entif-AI/Bilqis-MLX/commit/2391a8a431055512c9c8b7515d9d138a4d9927e8))
* **factory:** adopt boolean profile at live boundary ([2f0cea1](https://github.com/Entif-AI/Bilqis-MLX/commit/2f0cea186b3f6dfc273accfeb1b085baafe2b0ec))
* **factory:** bind autonomy to typed composition coverage ([a4e89f4](https://github.com/Entif-AI/Bilqis-MLX/commit/a4e89f43b395c2df6590018e881f26d50381c089))
* **factory:** bind developmental targets to factory releases ([cb2ed54](https://github.com/Entif-AI/Bilqis-MLX/commit/cb2ed54ef50a7239d207f1c04fda4c70eb22983c))
* **factory:** bind profile constraints to providers ([6076cd4](https://github.com/Entif-AI/Bilqis-MLX/commit/6076cd405418b502ee91db7595b8415f67594d66))
* **factory:** bind understanding proofs into autonomy routing ([2a47b2f](https://github.com/Entif-AI/Bilqis-MLX/commit/2a47b2fc871b5df2f4999b67b3de4ca97f67c651))
* **factory:** complete generative curriculum cutover and trainer governance ([44b5436](https://github.com/Entif-AI/Bilqis-MLX/commit/44b5436976362b4af3dcc93efc9c0fb5f1178b7d))
* **factory:** consume executable release for generation ([efd552d](https://github.com/Entif-AI/Bilqis-MLX/commit/efd552df8c851488dbfcf87ef473a4d4aaa8ca0a))
* **factory:** derive exact assessment scope identity ([7c24868](https://github.com/Entif-AI/Bilqis-MLX/commit/7c2486878e58972f0fdd11d6af8e8416b9ad4c0a))
* **factory:** encode post-boolean developmental staircase ([a8c07fd](https://github.com/Entif-AI/Bilqis-MLX/commit/a8c07fd9d1fe17a36fb3ce6970ccc8e0ffaa3f2f))
* **factory:** execute source-witnessed learner evidence ([6a0294e](https://github.com/Entif-AI/Bilqis-MLX/commit/6a0294ee25bb830b3af54e57ae86b819f9810a4c))
* **factory:** harden executable curriculum proof ([3169172](https://github.com/Entif-AI/Bilqis-MLX/commit/31691721448e7f8a26864bb19ca389c5d16e3cf8))
* **factory:** integrate executable closure with current recovery ([178e950](https://github.com/Entif-AI/Bilqis-MLX/commit/178e9509b73e62533efd376b035886768b7eda27))
* **factory:** persist verifiable semantic lineage ([d5e864a](https://github.com/Entif-AI/Bilqis-MLX/commit/d5e864a0a8a18846a83036559b3186c0cae6b688))
* **factory:** project curriculum prefixes by profile ([c2f80a4](https://github.com/Entif-AI/Bilqis-MLX/commit/c2f80a4867129803c5cb20f280092cf4320a0f8a))
* **factory:** route autonomous curriculum work ([1e6874f](https://github.com/Entif-AI/Bilqis-MLX/commit/1e6874f184403dbb5ba122c369a2c405286cd92f))
* **factory:** safely rebind autonomy evidence plans ([19ddea0](https://github.com/Entif-AI/Bilqis-MLX/commit/19ddea040247a47bf72bfabdacebde9c8499a178))
* **factory:** seal executable release v2 ([353e197](https://github.com/Entif-AI/Bilqis-MLX/commit/353e1976ad5d6ec18ba21c14c1ffc6a8bde12257))
* **factory:** separate catalog growth from curriculum identity ([63df955](https://github.com/Entif-AI/Bilqis-MLX/commit/63df955ee8aa8aedc2296cb889cf99aa680dd6e5))
* **factory:** stage candidate successors and advance source work ([b836afa](https://github.com/Entif-AI/Bilqis-MLX/commit/b836afa1cdff5d40f823938689f1780d585b3d1f))
* **factory:** to bilqis or bust ([19df489](https://github.com/Entif-AI/Bilqis-MLX/commit/19df4892ae8dfd278ee40b4f3de9d01becf8b393))
* **grade-b:** add composite boolean capability ([8b537eb](https://github.com/Entif-AI/Bilqis-MLX/commit/8b537ebd485b717a4f19304b28222caf00a78fca))
* **grade-b:** add inverse boolean identification ([a81716d](https://github.com/Entif-AI/Bilqis-MLX/commit/a81716d479e8f75d176aa79f0fa2de975961e3e0))
* **ingestion:** prove bounded real-source clean-room rebuild ([e8b0519](https://github.com/Entif-AI/Bilqis-MLX/commit/e8b05196904d9548e66fa344278dc62b2390d2d6))
* **ithkuil:** build source-grounded D-O curriculum frontier ([d425e91](https://github.com/Entif-AI/Bilqis-MLX/commit/d425e91c831a1a923680ee83fdb5bca9cdf49371))
* **ithkuil:** emit canonical extraction frontier receipt ([4d735e4](https://github.com/Entif-AI/Bilqis-MLX/commit/4d735e4583d4f9c6bed3340760f049e2fc7f6811))
* **ithkuil:** extract pinned affix source observations ([a32bde2](https://github.com/Entif-AI/Bilqis-MLX/commit/a32bde2542eb64399751ab4caf9bcd35302c43d8))
* **ithkuil:** merge source frontier into executable factory ([ac1ff2b](https://github.com/Entif-AI/Bilqis-MLX/commit/ac1ff2b87b0707d71a82f089ca1f5b8ef3a8c351))
* **ithkuil:** orchestrate optional owned graph readback ([00fc965](https://github.com/Entif-AI/Bilqis-MLX/commit/00fc9651fbecdc1b95a05e70eb535d92d0cfeabc))
* **ithkuil:** orchestrate pinned source ingestion ([91e7d97](https://github.com/Entif-AI/Bilqis-MLX/commit/91e7d979e04cc2f7d61dc279e0cc2a732aaecdca))
* **ithkuil:** orchestrate semantic build and conformance ([8a736c2](https://github.com/Entif-AI/Bilqis-MLX/commit/8a736c2f76a45843b494663dacb3a87b8653c0b0))
* **ithkuil:** parse lexicon chapters 1 and 2 ([4f4a1e0](https://github.com/Entif-AI/Bilqis-MLX/commit/4f4a1e0520570a3cd4399ae769d140e2ce736252))
* **ithkuil:** stage source-grounded copular identity through factory ([8c0de35](https://github.com/Entif-AI/Bilqis-MLX/commit/8c0de35a03d2ad8f2b089a35d60e2e99b0b38714))
* **jit:** if this works I am going to adopt an entire orphanage of abandoned tiny models ([bb71d6d](https://github.com/Entif-AI/Bilqis-MLX/commit/bb71d6dff50ee89b1d891cf1d8cb8ab915b5a55e))
* **memoization:** didja get that ting i sencha ([5d45472](https://github.com/Entif-AI/Bilqis-MLX/commit/5d4547269ebe4a05aaa6f57db436d89ef6fca7e3))
* **numeric:** rebind wide C to small staircase ([413239a](https://github.com/Entif-AI/Bilqis-MLX/commit/413239a186a2783948b02527a0b360d92a35fab9))
* **release:** expose trainer semver ([8e60e5d](https://github.com/Entif-AI/Bilqis-MLX/commit/8e60e5d1646ce5088453a9932ce7b075fc877823))
* **release:** reconcile source domains in a bound census ([5dc1c53](https://github.com/Entif-AI/Bilqis-MLX/commit/5dc1c53f33996d7001952d3bfee44f2b71dd7262))
* **runtime:** add restart-safe autonomous curriculum loop ([30eab01](https://github.com/Entif-AI/Bilqis-MLX/commit/30eab01a0a477c10ade471fc417f752fff2b3126))
* **runtime:** integrate main state, teaching and progression policies ([e80d5eb](https://github.com/Entif-AI/Bilqis-MLX/commit/e80d5ebef0d94f1522b12550ee4f3204832ad078))
* **runtime:** persist autonomous curriculum state ([f822d18](https://github.com/Entif-AI/Bilqis-MLX/commit/f822d18b6bf5defb9f5f1b826ce905e0ad65ebb5))
* **runtime:** teach after failed autonomous evidence ([4edb387](https://github.com/Entif-AI/Bilqis-MLX/commit/4edb387ebb014f217cd5967b303e9813306ce131))
* **sisyphus:** eternity is looking like a vacation compared to this ish ([c42ad91](https://github.com/Entif-AI/Bilqis-MLX/commit/c42ad916e94d375c73662025ea975118236f78f4))
* **skill:** package governed Ithkuil ingestion v1.0.0 ([efeb2a9](https://github.com/Entif-AI/Bilqis-MLX/commit/efeb2a985deef43b30114bc489ecdd5e4d8e5f99))
* **skos:** account for emitted held and unsupported source rows ([#42](https://github.com/Entif-AI/Bilqis-MLX/issues/42)) ([b6a2031](https://github.com/Entif-AI/Bilqis-MLX/commit/b6a20313f34f3ab65c35eb66d6f703e0fd6c38e8))
* **skos:** account for emitted held and unsupported source rows ([#42](https://github.com/Entif-AI/Bilqis-MLX/issues/42)) ([c2a1b30](https://github.com/Entif-AI/Bilqis-MLX/commit/c2a1b30fc11f2de649b7c1b04d5022eb0c20dd77))
* **skos:** add exact typed semantic lookup and repeatable indexes ([#76](https://github.com/Entif-AI/Bilqis-MLX/issues/76)) ([84ab6c8](https://github.com/Entif-AI/Bilqis-MLX/commit/84ab6c8524bd8f16163eadd62646cf441900a4f5))
* **skos:** added a SKOS-format ontology for New Ithkuil to change the world forever ([175cdf6](https://github.com/Entif-AI/Bilqis-MLX/commit/175cdf6778b4eeaea23a5bd36ad7dc6664df3ae8))
* **skos:** aggregate independent semantic conformance gates ([#72](https://github.com/Entif-AI/Bilqis-MLX/issues/72)) ([2e5eebc](https://github.com/Entif-AI/Bilqis-MLX/commit/2e5eebc0426901044dc78bf0c981d25d8cde557a))
* **skos:** bind public source loci to semantic resources ([#39](https://github.com/Entif-AI/Bilqis-MLX/issues/39)) ([4cf070c](https://github.com/Entif-AI/Bilqis-MLX/commit/4cf070c13ba1e413bbead1e3195383d1ea285a2b))
* **skos:** bind public source loci to semantic resources ([#39](https://github.com/Entif-AI/Bilqis-MLX/issues/39)) ([800efab](https://github.com/Entif-AI/Bilqis-MLX/commit/800efab21aa21953a84c5cbd371b5e8eaa0e4df7))
* **skos:** build source-qualified core RDF graphs ([#40](https://github.com/Entif-AI/Bilqis-MLX/issues/40)) ([6054127](https://github.com/Entif-AI/Bilqis-MLX/commit/6054127a40755c1dd67faca1c3b7df3c72adb7ef))
* **skos:** build source-qualified core RDF graphs ([#40](https://github.com/Entif-AI/Bilqis-MLX/issues/40)) ([a47ef72](https://github.com/Entif-AI/Bilqis-MLX/commit/a47ef7225fd338580c3ec598e6bc6aa52c95e29e))
* **skos:** canonicalize complete RDF graphs and bind digests ([#41](https://github.com/Entif-AI/Bilqis-MLX/issues/41)) ([24b779f](https://github.com/Entif-AI/Bilqis-MLX/commit/24b779f5ac492325bc1b7851f6b432e5438f01c2))
* **skos:** canonicalize complete RDF graphs and bind digests ([#41](https://github.com/Entif-AI/Bilqis-MLX/issues/41)) ([af428b0](https://github.com/Entif-AI/Bilqis-MLX/commit/af428b08dd3b658f5e8a1f6e6dd441bd097dded2))
* **skos:** compile every atomic category through one source pipeline ([#48](https://github.com/Entif-AI/Bilqis-MLX/issues/48)) ([62765c8](https://github.com/Entif-AI/Bilqis-MLX/commit/62765c8f27a922febc914289748fc9caf58f452d))
* **skos:** compile every atomic category through one source pipeline ([#48](https://github.com/Entif-AI/Bilqis-MLX/issues/48)) ([3123d58](https://github.com/Entif-AI/Bilqis-MLX/commit/3123d583f238a1d008bd8c2b1075cd48389b79d9))
* **skos:** compose whole-source coverage with visible semantic debt ([#68](https://github.com/Entif-AI/Bilqis-MLX/issues/68)) ([4aa51c5](https://github.com/Entif-AI/Bilqis-MLX/commit/4aa51c530c495fea78fd940292f353b5dedec6bb))
* **skos:** compose whole-source coverage with visible semantic debt ([#68](https://github.com/Entif-AI/Bilqis-MLX/issues/68)) ([38f69fd](https://github.com/Entif-AI/Bilqis-MLX/commit/38f69fd467ef825f5abb2d0ad84230599c2c8b64))
* **skos:** constrain semantic relations and extension admission ([#35](https://github.com/Entif-AI/Bilqis-MLX/issues/35)) ([d980f7d](https://github.com/Entif-AI/Bilqis-MLX/commit/d980f7dff55b5cf1eca65652becff5199ed45c62))
* **skos:** constrain semantic relations and extension admission ([#35](https://github.com/Entif-AI/Bilqis-MLX/issues/35)) ([cee1bef](https://github.com/Entif-AI/Bilqis-MLX/commit/cee1bef17fbc2706075a97eb168a41da3eb34f00))
* **skos:** define exact semantic coverage receipts ([#67](https://github.com/Entif-AI/Bilqis-MLX/issues/67)) ([1676c5b](https://github.com/Entif-AI/Bilqis-MLX/commit/1676c5bac16156cc28866540851d584e8f0d1b0e))
* **skos:** define exact semantic coverage receipts ([#67](https://github.com/Entif-AI/Bilqis-MLX/issues/67)) ([0a5820e](https://github.com/Entif-AI/Bilqis-MLX/commit/0a5820e4f632caadcfc8ffc2ea93310c2a279f60))
* **skos:** define lossless RDF to Falkor projection ([#73](https://github.com/Entif-AI/Bilqis-MLX/issues/73)) ([863baf0](https://github.com/Entif-AI/Bilqis-MLX/commit/863baf0d8f6c56dc8be9a7009e01d40246e7bb22))
* **skos:** define stable source-key namespace and identity contract ([#31](https://github.com/Entif-AI/Bilqis-MLX/issues/31)) ([4f8bf66](https://github.com/Entif-AI/Bilqis-MLX/commit/4f8bf66ef9280163068dddb6c7c7bdd1b27bcb1b))
* **skos:** emit reviewed mappings with precise conflict witnesses ([#63](https://github.com/Entif-AI/Bilqis-MLX/issues/63)) ([7a455e6](https://github.com/Entif-AI/Bilqis-MLX/commit/7a455e63537d03b428560430bdc1b699f66c8dd0))
* **skos:** emit reviewed mappings with precise conflict witnesses ([#63](https://github.com/Entif-AI/Bilqis-MLX/issues/63)) ([f0ccd14](https://github.com/Entif-AI/Bilqis-MLX/commit/f0ccd14047e3740450d6b617a0cd81b670448752))
* **skos:** enforce resource shapes and source-semantic ordering ([#32](https://github.com/Entif-AI/Bilqis-MLX/issues/32)) ([caf06a2](https://github.com/Entif-AI/Bilqis-MLX/commit/caf06a2a3c66cc02b2dae6ea1b57a9bc900d2ee9))
* **skos:** exact Unicode notation and collision contracts ([#33](https://github.com/Entif-AI/Bilqis-MLX/issues/33)) ([e6336c5](https://github.com/Entif-AI/Bilqis-MLX/commit/e6336c5b6020abe4c28d12f7aee6eb6c534601b7))
* **skos:** freeze minimal source-proven extension vocabulary ([#60](https://github.com/Entif-AI/Bilqis-MLX/issues/60)) ([57526b9](https://github.com/Entif-AI/Bilqis-MLX/commit/57526b9112a7d5c4cd5f244565130883764f24f0))
* **skos:** freeze minimal source-proven extension vocabulary ([#60](https://github.com/Entif-AI/Bilqis-MLX/issues/60)) ([99b4455](https://github.com/Entif-AI/Bilqis-MLX/commit/99b4455409d750d1b998c51e633049a94e9772b3))
* **skos:** freeze read-only semantic smoke queries ([#77](https://github.com/Entif-AI/Bilqis-MLX/issues/77)) ([a1f20e6](https://github.com/Entif-AI/Bilqis-MLX/commit/a1f20e649064c7be1d384f0ea520d1e78a17a3cc))
* **skos:** guard owned reset against foreign and stale boundaries ([#75](https://github.com/Entif-AI/Bilqis-MLX/issues/75)) ([a113123](https://github.com/Entif-AI/Bilqis-MLX/commit/a11312355ecd3ca363568ad11ef42dc4a7ba6288))
* **skos:** i got skos a hos fo gardening yo ([f47e171](https://github.com/Entif-AI/Bilqis-MLX/commit/f47e171a79edcba4a5d6daa80f1e1c4550313afa))
* **skos:** import conformant RDF idempotently into owned Falkor graphs ([#74](https://github.com/Entif-AI/Bilqis-MLX/issues/74)) ([f05ed09](https://github.com/Entif-AI/Bilqis-MLX/commit/f05ed09409e498d7f960768d27118fbcf1858cd5))
* **skos:** model source-faithful composition resources ([#57](https://github.com/Entif-AI/Bilqis-MLX/issues/57)) ([38e2df0](https://github.com/Entif-AI/Bilqis-MLX/commit/38e2df06da75d93ed8d712147a04b6d5e11a1d1e))
* **skos:** model source-faithful composition resources ([#57](https://github.com/Entif-AI/Bilqis-MLX/issues/57)) ([75f43e1](https://github.com/Entif-AI/Bilqis-MLX/commit/75f43e1661421bc8c2bf2853f0a1fc1ff46ce114))
* **skos:** normalize source-grounded atomic definitions ([#46](https://github.com/Entif-AI/Bilqis-MLX/issues/46)) ([eea3e29](https://github.com/Entif-AI/Bilqis-MLX/commit/eea3e2980b17b50163e767441aa67779da4c5faa))
* **skos:** normalize source-grounded atomic definitions ([#46](https://github.com/Entif-AI/Bilqis-MLX/issues/46)) ([9ec44f6](https://github.com/Entif-AI/Bilqis-MLX/commit/9ec44f65ef5bf812d0d9d64edf583a15afe3e58d))
* **skos:** parse Chapter 4 lexicon frontier ([ad3c8a3](https://github.com/Entif-AI/Bilqis-MLX/commit/ad3c8a3481390ecba1853a2d179d0ddce7462b4e))
* **skos:** parse Chapter 5 lexicon frontier ([52cd8ab](https://github.com/Entif-AI/Bilqis-MLX/commit/52cd8ab3b5f8cd4b2fbab6fb84351f6cba3a7a06))
* **skos:** parse Chapter 6 lexicon frontier ([7f403bd](https://github.com/Entif-AI/Bilqis-MLX/commit/7f403bd3971d91b9bd633b3898e7f6d9348c21c9))
* **skos:** parse Chapter 7 lexicon frontier ([b0a9a0d](https://github.com/Entif-AI/Bilqis-MLX/commit/b0a9a0d47db67f77bd4dd56fafe48c01a5711aa3))
* **skos:** preserve explicit source allomorph rules ([#59](https://github.com/Entif-AI/Bilqis-MLX/issues/59)) ([6cc215f](https://github.com/Entif-AI/Bilqis-MLX/commit/6cc215f0fb8fe29ab01e346b0b064832dc342416))
* **skos:** preserve explicit source allomorph rules ([#59](https://github.com/Entif-AI/Bilqis-MLX/issues/59)) ([f9d11e2](https://github.com/Entif-AI/Bilqis-MLX/commit/f9d11e2239aa500b93f22eb646cd8a5738e118bb))
* **skos:** preserve held mapping states and screen encoded private text ([#64](https://github.com/Entif-AI/Bilqis-MLX/issues/64)) ([0cf5db2](https://github.com/Entif-AI/Bilqis-MLX/commit/0cf5db29a6c57a87b7ee9d282d9f49897dd0e815))
* **skos:** preserve held mapping states and screen encoded private text ([#64](https://github.com/Entif-AI/Bilqis-MLX/issues/64)) ([8b15c82](https://github.com/Entif-AI/Bilqis-MLX/commit/8b15c82f61fedca58cec3d4f4b00fd97a4c35ed6))
* **skos:** preserve ordered linguistic composition components ([#58](https://github.com/Entif-AI/Bilqis-MLX/issues/58)) ([b645091](https://github.com/Entif-AI/Bilqis-MLX/commit/b6450913c7cb43a2ced713c6ebf969c05a85e0dc))
* **skos:** preserve ordered linguistic composition components ([#58](https://github.com/Entif-AI/Bilqis-MLX/issues/58)) ([4df2049](https://github.com/Entif-AI/Bilqis-MLX/commit/4df2049b20abfecc2d4b1a73422439cd31959a05))
* **skos:** preserve source realizations under stable identity ([#45](https://github.com/Entif-AI/Bilqis-MLX/issues/45)) ([85e483e](https://github.com/Entif-AI/Bilqis-MLX/commit/85e483ee32d84094de2f400d65fb75328b769e37))
* **skos:** preserve source realizations under stable identity ([#45](https://github.com/Entif-AI/Bilqis-MLX/issues/45)) ([48a40ae](https://github.com/Entif-AI/Bilqis-MLX/commit/48a40ae0789b67e01ce0477892d2f1e827906786))
* **skos:** preserve stable independently addressable senses ([#51](https://github.com/Entif-AI/Bilqis-MLX/issues/51)) ([3a56941](https://github.com/Entif-AI/Bilqis-MLX/commit/3a56941fef5552177c182c6201ae90c2132f75b9))
* **skos:** preserve stable independently addressable senses ([#51](https://github.com/Entif-AI/Bilqis-MLX/issues/51)) ([a81e24b](https://github.com/Entif-AI/Bilqis-MLX/commit/a81e24b7b771852ac74f59bf44330b41ed8cde17))
* **skos:** preserve typed Unicode notation and report collisions ([#33](https://github.com/Entif-AI/Bilqis-MLX/issues/33)) ([d217a35](https://github.com/Entif-AI/Bilqis-MLX/commit/d217a3579b7d801adcefc610343f2af301213e31))
* **skos:** project source-qualified affix-degree concepts ([#56](https://github.com/Entif-AI/Bilqis-MLX/issues/56)) ([a86df50](https://github.com/Entif-AI/Bilqis-MLX/commit/a86df50fdb80c9688e9e64d015411f5c2225316c))
* **skos:** project source-qualified affix-degree concepts ([#56](https://github.com/Entif-AI/Bilqis-MLX/issues/56)) ([5d1bd00](https://github.com/Entif-AI/Bilqis-MLX/commit/5d1bd00fb955019b7557de502f3e5ee15ac32f6b))
* **skos:** project source-qualified lexicon roots ([#50](https://github.com/Entif-AI/Bilqis-MLX/issues/50)) ([39fd084](https://github.com/Entif-AI/Bilqis-MLX/commit/39fd084c368c35aca3f468898b3f79f01e818075))
* **skos:** project source-qualified lexicon roots ([#50](https://github.com/Entif-AI/Bilqis-MLX/issues/50)) ([65db1c4](https://github.com/Entif-AI/Bilqis-MLX/commit/65db1c45d7edf4ebf87b7c4ab264d79dbf7e3f31))
* **skos:** prove a receipt-checked read-only Akasha path ([#79](https://github.com/Entif-AI/Bilqis-MLX/issues/79)) ([6cd231e](https://github.com/Entif-AI/Bilqis-MLX/commit/6cd231ec8a0707b65781644428382b154940e145))
* **skos:** publish reproducible RDF and held-ledger generations ([#43](https://github.com/Entif-AI/Bilqis-MLX/issues/43)) ([c629439](https://github.com/Entif-AI/Bilqis-MLX/commit/c629439126238d0a6cbcc46944417f1bb3408403))
* **skos:** publish reproducible RDF and held-ledger generations ([#43](https://github.com/Entif-AI/Bilqis-MLX/issues/43)) ([850e35e](https://github.com/Entif-AI/Bilqis-MLX/commit/850e35ec3a12257450f335a1afca1dfaad4f20c6))
* **skos:** qualify finite mapping admissions ([#62](https://github.com/Entif-AI/Bilqis-MLX/issues/62)) ([419ebf9](https://github.com/Entif-AI/Bilqis-MLX/commit/419ebf94fdf8915b63a1391ba3fbf2345a1bead9))
* **skos:** qualify finite mapping admissions ([#62](https://github.com/Entif-AI/Bilqis-MLX/issues/62)) ([b4f42f7](https://github.com/Entif-AI/Bilqis-MLX/commit/b4f42f7803c4bf28c9f08da505eae03f506213f6))
* **skos:** qualify minimal root-to-sense relation ([#53](https://github.com/Entif-AI/Bilqis-MLX/issues/53)) ([13a3605](https://github.com/Entif-AI/Bilqis-MLX/commit/13a36050690b0e394a6c93d5ad9bdfa4a75f04b4))
* **skos:** qualify minimal root-to-sense relation ([#53](https://github.com/Entif-AI/Bilqis-MLX/issues/53)) ([cb2a6e9](https://github.com/Entif-AI/Bilqis-MLX/commit/cb2a6e90147462896ae66617f120e95eee4dcf83))
* **skos:** reconcile all linguistic residue source rows ([#61](https://github.com/Entif-AI/Bilqis-MLX/issues/61)) ([862febb](https://github.com/Entif-AI/Bilqis-MLX/commit/862febbf61bd487ea37138555076fcbc7c150dad))
* **skos:** reconcile all linguistic residue source rows ([#61](https://github.com/Entif-AI/Bilqis-MLX/issues/61)) ([3abd738](https://github.com/Entif-AI/Bilqis-MLX/commit/3abd738e6d4f1ae28bf995aaa287de8ad66e6e9f))
* **skos:** reconcile complete atomic source and RDF coverage ([#49](https://github.com/Entif-AI/Bilqis-MLX/issues/49)) ([800e11e](https://github.com/Entif-AI/Bilqis-MLX/commit/800e11e9e8c451b3ea0295af6f2424ea43763b84))
* **skos:** reconcile complete atomic source and RDF coverage ([#49](https://github.com/Entif-AI/Bilqis-MLX/issues/49)) ([5606187](https://github.com/Entif-AI/Bilqis-MLX/commit/56061875da47270aeb04dabb26ba4313f0324f25))
* **skos:** reconcile current root and sense frontier ([#55](https://github.com/Entif-AI/Bilqis-MLX/issues/55)) ([ea975f9](https://github.com/Entif-AI/Bilqis-MLX/commit/ea975f9b374b5c6730539e0fdac4915414382720))
* **skos:** reconcile current root and sense frontier ([#55](https://github.com/Entif-AI/Bilqis-MLX/issues/55)) ([fe858f3](https://github.com/Entif-AI/Bilqis-MLX/commit/fe858f3cc4c4346e9349b4034a2672880d21f9ed))
* **skos:** reconcile every mapping source row and assertion ([#66](https://github.com/Entif-AI/Bilqis-MLX/issues/66)) ([e04533a](https://github.com/Entif-AI/Bilqis-MLX/commit/e04533ae1328f15c4815a27862df91f7e3ce57da))
* **skos:** reconcile every mapping source row and assertion ([#66](https://github.com/Entif-AI/Bilqis-MLX/issues/66)) ([f994eac](https://github.com/Entif-AI/Bilqis-MLX/commit/f994eac6bc354c2b6f52233d962dc6c5b1a618d1))
* **skos:** reject impossible endpoints and contradictory mapping claims ([#65](https://github.com/Entif-AI/Bilqis-MLX/issues/65)) ([74f0e4a](https://github.com/Entif-AI/Bilqis-MLX/commit/74f0e4ab901a6cd7c0c9d32746e220cae418acec))
* **skos:** reject impossible endpoints and contradictory mapping claims ([#65](https://github.com/Entif-AI/Bilqis-MLX/issues/65)) ([71002f4](https://github.com/Entif-AI/Bilqis-MLX/commit/71002f46e0907937a7a10827f2ea9fc6f91d7176))
* **skos:** reject silent semantic omissions using independent source IDs ([#69](https://github.com/Entif-AI/Bilqis-MLX/issues/69)) ([936c251](https://github.com/Entif-AI/Bilqis-MLX/commit/936c251ea307f5ac814579a38b1b2259101c3544))
* **skos:** reject silent semantic omissions using independent source IDs ([#69](https://github.com/Entif-AI/Bilqis-MLX/issues/69)) ([6df38a2](https://github.com/Entif-AI/Bilqis-MLX/commit/6df38a24829c6c81c67152eecf93cd45fcd663f5))
* **skos:** report exact notation collisions and qualified homographs ([#47](https://github.com/Entif-AI/Bilqis-MLX/issues/47)) ([2d296c5](https://github.com/Entif-AI/Bilqis-MLX/commit/2d296c50eaa2e07157ecd4b37658b2b25f96d8d1))
* **skos:** report exact notation collisions and qualified homographs ([#47](https://github.com/Entif-AI/Bilqis-MLX/issues/47)) ([783b9db](https://github.com/Entif-AI/Bilqis-MLX/commit/783b9db43595424d38b8d15a56d2be14276f59e5))
* **skos:** require smoke-backed materialization receipts ([#78](https://github.com/Entif-AI/Bilqis-MLX/issues/78)) ([8768876](https://github.com/Entif-AI/Bilqis-MLX/commit/8768876c7283bab014ff9c0f54edd0569b124251))
* **skos:** resolve source identities and preserve realization evidence ([#38](https://github.com/Entif-AI/Bilqis-MLX/issues/38)) ([cc64fb8](https://github.com/Entif-AI/Bilqis-MLX/commit/cc64fb889debace52863a9d8002a9681aed4bf23))
* **skos:** resolve source identities and preserve realization evidence ([#38](https://github.com/Entif-AI/Bilqis-MLX/issues/38)) ([c855942](https://github.com/Entif-AI/Bilqis-MLX/commit/c8559426bfe1f406f00c466ace75c522e03eefd3))
* **skos:** resource shapes and source-semantic order ([#32](https://github.com/Entif-AI/Bilqis-MLX/issues/32)) ([9a51115](https://github.com/Entif-AI/Bilqis-MLX/commit/9a51115cc43a91f602d59ad6d7eb87ac4d4aad5e))
* **skos:** retain Stem and Specification dimensions ([#52](https://github.com/Entif-AI/Bilqis-MLX/issues/52)) ([c8d755a](https://github.com/Entif-AI/Bilqis-MLX/commit/c8d755ab1098f0b6ab0d40943a5491c5354a24f1))
* **skos:** retain Stem and Specification dimensions ([#52](https://github.com/Entif-AI/Bilqis-MLX/issues/52)) ([603c97b](https://github.com/Entif-AI/Bilqis-MLX/commit/603c97bf0d1af1e570c7fe05d80358473de4c18f))
* **skos:** source-grounded labels and documentation ([#34](https://github.com/Entif-AI/Bilqis-MLX/issues/34)) ([001f88c](https://github.com/Entif-AI/Bilqis-MLX/commit/001f88c5bb4129b1f8fdb53915b703ec9ce992ef))
* **skos:** source-grounded labels and documentation ([#34](https://github.com/Entif-AI/Bilqis-MLX/issues/34)) ([5dc97b1](https://github.com/Entif-AI/Bilqis-MLX/commit/5dc97b1f90d8dae440080696792417ef26159b43))
* **skos:** source-qualified mapping strengths and conflict checks ([#36](https://github.com/Entif-AI/Bilqis-MLX/issues/36)) ([b944957](https://github.com/Entif-AI/Bilqis-MLX/commit/b944957ccf96ab806f7538afb8cf2236d6efad87))
* **skos:** source-qualified mapping strengths and conflict checks ([#36](https://github.com/Entif-AI/Bilqis-MLX/issues/36)) ([ac9589d](https://github.com/Entif-AI/Bilqis-MLX/commit/ac9589d08d943710d868f5184d71307d729e54e5))
* **skos:** stable namespace and source-coordinate identities ([#31](https://github.com/Entif-AI/Bilqis-MLX/issues/31)) ([82baca2](https://github.com/Entif-AI/Bilqis-MLX/commit/82baca22003e0a77171cdd01f3cd6888f2484047))
* **skos:** validate proven RDF invariants with SHACL ([#71](https://github.com/Entif-AI/Bilqis-MLX/issues/71)) ([5592927](https://github.com/Entif-AI/Bilqis-MLX/commit/5592927532240dedaec93450487624f38d340b73))
* **skos:** validate tracked CSV compiler inputs ([#37](https://github.com/Entif-AI/Bilqis-MLX/issues/37)) ([bd20380](https://github.com/Entif-AI/Bilqis-MLX/commit/bd20380602610133b8ce631a210472d7420add62))
* **skos:** validate tracked CSV compiler inputs ([#37](https://github.com/Entif-AI/Bilqis-MLX/issues/37)) ([7339b71](https://github.com/Entif-AI/Bilqis-MLX/commit/7339b713f2e56c0d54f960e45d289e7dec3179d3))
* **skos:** verify exact RDF rebuild equivalence and typed lexical fidelity ([#70](https://github.com/Entif-AI/Bilqis-MLX/issues/70)) ([8b14e4d](https://github.com/Entif-AI/Bilqis-MLX/commit/8b14e4d727a92c890dcec8228880fc5757e2ae06))
* **skos:** verify exact RDF rebuild equivalence and typed lexical fidelity ([#70](https://github.com/Entif-AI/Bilqis-MLX/issues/70)) ([ebfb9ad](https://github.com/Entif-AI/Bilqis-MLX/commit/ebfb9adcd0c3b2dbcf59b3d924593c70f93f3664))
* **teacher:** add vnext shadow proposal control ([e7f811e](https://github.com/Entif-AI/Bilqis-MLX/commit/e7f811eaec6aef4ef3bb042f3e2d98628b23c285))
* **teacher:** condition lessons on weakest semantics ([cf73bb9](https://github.com/Entif-AI/Bilqis-MLX/commit/cf73bb96a6faf2ab59ba820bfde0c8970b936c4f))
* **teacher:** grant bounded vnext canary authority ([ee64915](https://github.com/Entif-AI/Bilqis-MLX/commit/ee6491544685ffc81cc75bc755339ecd615ae58d))
* **teaching:** admit source-checked prerequisite contrasts in shared lessons ([b993bb6](https://github.com/Entif-AI/Bilqis-MLX/commit/b993bb6c0d2e48820a152d011b3827cecece9a23))
* **teaching:** contrast event roots over identical source worlds ([cb05878](https://github.com/Entif-AI/Bilqis-MLX/commit/cb0587876e5856e17c9a9841c346bc2cae4c9617))
* **teaching:** reuse simple event observations beside root contrasts ([d7668b8](https://github.com/Entif-AI/Bilqis-MLX/commit/d7668b8b18f27d4b99f9733573dc17e2fbbe52cd))
* **trainer:** add B boolean association bridge ([7e5b19a](https://github.com/Entif-AI/Bilqis-MLX/commit/7e5b19afa58b36420e32d33978ff781e430fa44c))
* **trainer:** add high-resolution timing trace ([51e4389](https://github.com/Entif-AI/Bilqis-MLX/commit/51e43891073ae01104a399cedc25b30e3817a466))
* **trainer:** add human-authorized autonomous curriculum mode ([5f76eba](https://github.com/Entif-AI/Bilqis-MLX/commit/5f76eba72bae038904fa642b9e5fc591a2096fc0))
* **trainer:** add non-authoritative flash mode ([afb3d2b](https://github.com/Entif-AI/Bilqis-MLX/commit/afb3d2b864262f498b542e84d907babf87fef728))
* **trainer:** continue Grade C numeric staircase ([eaa579e](https://github.com/Entif-AI/Bilqis-MLX/commit/eaa579e669aebb5f5e9e157c652c3c9196b0a709))
* use direct U7C boolean lessons ([b579355](https://github.com/Entif-AI/Bilqis-MLX/commit/b5793556a4e652e03e8392adc59a69f3840e590a))


### Bug Fixes

* **assessment:** burn cohorts without exhausting specimens ([69e71b3](https://github.com/Entif-AI/Bilqis-MLX/commit/69e71b3804083feb829787cac2f627cd8379c60e))
* **assessment:** keep cumulative rubric through quarantine ([ca938eb](https://github.com/Entif-AI/Bilqis-MLX/commit/ca938eb545ac63f4951a71eea1c32dc21befbaa0))
* **assessment:** seal exams by represented grade scope ([7ef1369](https://github.com/Entif-AI/Bilqis-MLX/commit/7ef1369d59bea2d4ebe0daf01005336e43f5c56e))
* **assessment:** separate scope seals from cohort provenance ([20e7713](https://github.com/Entif-AI/Bilqis-MLX/commit/20e771322387fdf80d2dec909f778627e4dcd09c))
* **assessment:** verify burned cohorts by historical release ([2a33a99](https://github.com/Entif-AI/Bilqis-MLX/commit/2a33a996a9db9bd7163b5185c0dfbd4d493debce))
* **autonomy:** support current minimal b runtime ([00961ad](https://github.com/Entif-AI/Bilqis-MLX/commit/00961ad2c96923ed054b07d619126deb1166d398))
* centralize stored cohort verification ([5017176](https://github.com/Entif-AI/Bilqis-MLX/commit/5017176a1cc6de78f74c6e83f46265232f0236a7))
* **championship:** allow subperfect mentor roles ([a5613df](https://github.com/Entif-AI/Bilqis-MLX/commit/a5613df46c47e846dbe4fd87a920976099e6254f))
* **championships:** complete rev7 governance acceptance ([a632810](https://github.com/Entif-AI/Bilqis-MLX/commit/a632810dcf4d1d08c56372d95bbf6f225e29d524))
* **championships:** inherit earning exams across champion lineages ([7d879a9](https://github.com/Entif-AI/Bilqis-MLX/commit/7d879a9920df9fc3d987c485580c0e2885f8f7ea))
* **championships:** preserve idboolops prefix compatibility ([3409894](https://github.com/Entif-AI/Bilqis-MLX/commit/3409894e59e66f766b53c2aaf91ca7684d6fd49d))
* **champions:** require strict incumbent battery win ([fcbe496](https://github.com/Entif-AI/Bilqis-MLX/commit/fcbe4969ae4e44956b40054b6181f20abf931e07))
* **champions:** score checkpoint-origin grade panel ([6974333](https://github.com/Entif-AI/Bilqis-MLX/commit/697433311a973fbf2b7ecd182f52f7893cdc2c72))
* **champions:** separate title grade from checkpoint origin ([6e04ca0](https://github.com/Entif-AI/Bilqis-MLX/commit/6e04ca0df261a859111f6a39b145a8fa6ed81a55))
* **ci:** install Falkor dependencies for SKOS test discovery ([92494c3](https://github.com/Entif-AI/Bilqis-MLX/commit/92494c3b8792cc6f3b962852da1cb6eff41cbd35))
* **ci:** install full SKOS proof dependencies ([ffb599e](https://github.com/Entif-AI/Bilqis-MLX/commit/ffb599e1ad17f9f85edd02d613989917c6ec93af))
* **ci:** keep symbolic source probes torch-free ([d02d8cb](https://github.com/Entif-AI/Bilqis-MLX/commit/d02d8cbcdd21d9f9131b2d6889c0a24bf5acaf9d))
* **ci:** name historical operator contracts without altering semantics ([cae7a81](https://github.com/Entif-AI/Bilqis-MLX/commit/cae7a81a9c53d2ef502baff923e6d355b66811c7))
* **ci:** repair merge verification after repo reorg ([f29f2ef](https://github.com/Entif-AI/Bilqis-MLX/commit/f29f2efc13fa8b2c808dc289019006ade23f9d09))
* **ci:** separate portable SKOS checks from release proof ([36b5c2b](https://github.com/Entif-AI/Bilqis-MLX/commit/36b5c2b954290264e24ff0e47b64a555ef9291bb))
* **cli:** expose registered error explanations in canonical checkout ([b0cf670](https://github.com/Entif-AI/Bilqis-MLX/commit/b0cf6701d925863ca39e32a8f3463acc6d262631))
* **code-smell:** chocolate rain... I move my mouth away from the mic to breathe ([135c8db](https://github.com/Entif-AI/Bilqis-MLX/commit/135c8db7ea98f14c1d3af958e639821c0462c57a))
* **compat:** recover erased settlement ledger ([2a9ebef](https://github.com/Entif-AI/Bilqis-MLX/commit/2a9ebefe5d2d9337b718e1016a191027aad413cf))
* **curriculum:** add promotion sweep hysteresis ([768e36e](https://github.com/Entif-AI/Bilqis-MLX/commit/768e36eabcdb790c5fa6fb2e9fa793efca23782d))
* **curriculum:** align idboolops successor preflight ([0dcaf6c](https://github.com/Entif-AI/Bilqis-MLX/commit/0dcaf6cf7b10d97b255ec5bc422bd6f25df3b823))
* **curriculum:** allow debt progression on introduced assessment scope ([15e28af](https://github.com/Entif-AI/Bilqis-MLX/commit/15e28af3a884e0457d35fea207a02f46f82d8df9))
* **curriculum:** declare staged boolean abstraction dependencies ([192dc8f](https://github.com/Entif-AI/Bilqis-MLX/commit/192dc8fbafe5eaa72159f9597a729705b716e532))
* **curriculum:** migrate promoted C numeric ceiling ([80a49d0](https://github.com/Entif-AI/Bilqis-MLX/commit/80a49d01f484d56917d8b9427037e31a754da243))
* **curriculum:** preserve cohort custody across debt transitions ([dba4edd](https://github.com/Entif-AI/Bilqis-MLX/commit/dba4edda781ed32ed33e6faf4e7898c8645b0a43))
* **curriculum:** preserve grade C and diagnostics reads after mean promotion ([5ed9ea6](https://github.com/Entif-AI/Bilqis-MLX/commit/5ed9ea624b9c9a0e22052c78cb884a533fb4abdc))
* **curriculum:** prioritize admitted frontier over earlier mastery debt ([fdcf3cb](https://github.com/Entif-AI/Bilqis-MLX/commit/fdcf3cb8d7420f8f0123a951bcd539bf17ce6bbf))
* **curriculum:** revisit imperfect earlier grades during C staging ([d7dcdaf](https://github.com/Entif-AI/Bilqis-MLX/commit/d7dcdafe43982803793901e0e9bed19f029afc54))
* **curriculum:** separate championship source context ([bf3ef84](https://github.com/Entif-AI/Bilqis-MLX/commit/bf3ef84c24ca61ebc48865396f43ed656e43e3a6))
* **curriculum:** validate withheld evidence by its sealed scope ([5ea41b9](https://github.com/Entif-AI/Bilqis-MLX/commit/5ea41b90ab1873b65dcec4c41303fcd987c9fdf2))
* **curriculum:** winnow existing full grade b on resume ([15e761b](https://github.com/Entif-AI/Bilqis-MLX/commit/15e761b4fdcbc0c90f6dd41c7b28c0a62675e0fd))
* **custody:** authenticate archived matchup repair event before recovery ([c07814e](https://github.com/Entif-AI/Bilqis-MLX/commit/c07814e34919bbd5eb79d0c549a71cc6ea13c9b2))
* **dashboard:** align latest grade and champion scores ([e969111](https://github.com/Entif-AI/Bilqis-MLX/commit/e969111032e48782c3ab73e5a023f52ab8362e4d))
* **dashboard:** compress integer root scope ([c9ed590](https://github.com/Entif-AI/Bilqis-MLX/commit/c9ed590d5222972ae7026597c72896cf9464ec17))
* **dashboard:** feed live attempted throughput ([b4be18b](https://github.com/Entif-AI/Bilqis-MLX/commit/b4be18b427951a8d87105886af0edd74bdcdbf01))
* **dashboard:** follow active training journal across worktrees ([f362af4](https://github.com/Entif-AI/Bilqis-MLX/commit/f362af498e4e0e6647c9589135a988f59c041682))
* **dashboard:** keep live training telemetry current ([a019475](https://github.com/Entif-AI/Bilqis-MLX/commit/a01947589fb2f3742e5ec63ddbf20f461f271e01))
* **dashboard:** preserve all active champions ([51f8702](https://github.com/Entif-AI/Bilqis-MLX/commit/51f87023da5db4ffff1f829ad4e59fba35d0f482))
* **dashboard:** render omitted target grade ([06d1dde](https://github.com/Entif-AI/Bilqis-MLX/commit/06d1ddef12ef8f873b5635e90ed215701cd018ae))
* **dashboard:** report attempted steps per minute ([e0b8894](https://github.com/Entif-AI/Bilqis-MLX/commit/e0b88947b4cbeb27596daf0064d749d4f28caf06))
* **dashboard:** reset command-local visit counter ([f474dae](https://github.com/Entif-AI/Bilqis-MLX/commit/f474dae5da5a2fa070495c995589f0a9c92cea6d))
* **dashboard:** reset command-local visit counter ([aac2a0b](https://github.com/Entif-AI/Bilqis-MLX/commit/aac2a0b99f78028141e4ed040bdbd2456a280993))
* **dashboard:** resolve DAG champion state ([efd73cc](https://github.com/Entif-AI/Bilqis-MLX/commit/efd73cc54edf2fadc3a62aaa7123349cfb091636))
* **dashboard:** resolve DAG champion state ([30d3735](https://github.com/Entif-AI/Bilqis-MLX/commit/30d3735c2691dd10e2e3def92a7e96715f6e35de))
* **dashboard:** stabilize steps per minute ([79efeaf](https://github.com/Entif-AI/Bilqis-MLX/commit/79efeaf5a94d89a1432075e1b14647ef01e1aa4e))
* **dashboard:** updated watch feature ([78f65c4](https://github.com/Entif-AI/Bilqis-MLX/commit/78f65c4101eed7d58ac665bb7498bd1a1a184539))
* **events:** tolerate legacy ledger ids ([eab5354](https://github.com/Entif-AI/Bilqis-MLX/commit/eab5354da3c2eab3c599a8f72dedfa9ff1ddd419))
* **events:** tolerate legacy ledger ids ([1e03392](https://github.com/Entif-AI/Bilqis-MLX/commit/1e033925d5215802800cfdc93f1d3a8c28793443))
* **experiment:** harden Ithkuil grammar extraction ([c89a509](https://github.com/Entif-AI/Bilqis-MLX/commit/c89a50973f5a437cc9364bc045b32a04522bbd9f))
* **factory:** bind v2 structural witness curriculum ([4d2b34d](https://github.com/Entif-AI/Bilqis-MLX/commit/4d2b34dbabb04c378e52fb5dcef113218e5037a2))
* **factory:** defer speculative composition candidates ([d6ab17a](https://github.com/Entif-AI/Bilqis-MLX/commit/d6ab17acfe297b96bdfda3045153a811b12c1e16))
* **factory:** preserve numeric scope contract through integration ([6796270](https://github.com/Entif-AI/Bilqis-MLX/commit/6796270af6110cd40c5d39db96d6a05209584484))
* **factory:** preserve released boolean course contracts ([935fb71](https://github.com/Entif-AI/Bilqis-MLX/commit/935fb711475b891da8a0a54c42d546ac2c5c99c3))
* **factory:** requalify compatible released providers ([f8bf10e](https://github.com/Entif-AI/Bilqis-MLX/commit/f8bf10e9bb07a7cde93217861b762b74cd90cec1))
* **factory:** require exact developmental prerequisites ([8548fb3](https://github.com/Entif-AI/Bilqis-MLX/commit/8548fb3fa46448f5d1d4b2762fd1315abdfdf040))
* **governance:** retire speculative resets, verify cohort provenance and retain settlements ([b1a0235](https://github.com/Entif-AI/Bilqis-MLX/commit/b1a02358325f85af322b710f93f2e5ec20253e4f))
* **grade-b:** accept unbalanced replay cohorts ([65d6ebc](https://github.com/Entif-AI/Bilqis-MLX/commit/65d6ebc7d749dea6f81a89e1356eb5d5025e6918))
* **grade-b:** admit full U7C predicate set safely ([2ed45db](https://github.com/Entif-AI/Bilqis-MLX/commit/2ed45dbeb7965b45bf48207710e3e033c2f92916))
* **grade-b:** binary ternary quadrary quinn rarely ([a4e3913](https://github.com/Entif-AI/Bilqis-MLX/commit/a4e3913c1e0001b037324b5f0088bf1bd9f62d5b))
* **grade-b:** remove idboolops arity leakage ([5c44f2c](https://github.com/Entif-AI/Bilqis-MLX/commit/5c44f2cc0237312dae03673d428de359b78a1efa))
* **ingestion:** normalize excerpt wrapper whitespace and refresh proof ([effa5dc](https://github.com/Entif-AI/Bilqis-MLX/commit/effa5dc8aa3c1a7a1eda02fb9a7f66b8a5690463))
* **integration:** retain numeric wire contract and owned runtime helpers ([0c6f5e1](https://github.com/Entif-AI/Bilqis-MLX/commit/0c6f5e1310d2e5609e243594fa3b9adb6b294e4c))
* interpret saved cohort digests by schema ([0727ea9](https://github.com/Entif-AI/Bilqis-MLX/commit/0727ea9f8ea23831b7f318ef8b491b9183fbf5cc))
* **ithkuil:** repair relocated source library paths ([795f280](https://github.com/Entif-AI/Bilqis-MLX/commit/795f28079da59d8d45750df1acc49aa339d9cbae))
* **learning:** enable event trials and rehearse carried mastery debt ([5ccc8b1](https://github.com/Entif-AI/Bilqis-MLX/commit/5ccc8b16a7440d922215c51c4e5dec472a779db4))
* **mentors:** let maxed roles advise across grades ([38e6385](https://github.com/Entif-AI/Bilqis-MLX/commit/38e63852b85ac2c560b9dfa8a63e7a05b4475fa0))
* **mentors:** route role-owner advice by capability ([b82f6f3](https://github.com/Entif-AI/Bilqis-MLX/commit/b82f6f3ab112f0cb9645720a75b477e5be55b8d3))
* **mlx:** memory leak fixed in mlx ([de128d5](https://github.com/Entif-AI/Bilqis-MLX/commit/de128d5f5d9dde44185285737ca4951e3b02f1f7))
* **numeric:** keep epoch history typed across rebind ([b79677e](https://github.com/Entif-AI/Bilqis-MLX/commit/b79677e34e82358a838b4a50bcebcead7f4143ce))
* **numeric:** reconcile debt on profile contraction ([f88c8ca](https://github.com/Entif-AI/Bilqis-MLX/commit/f88c8caf122f06e7a487ebad742ad98a7f0b9027))
* **numeric:** repair malformed epoch history on resume ([4c1bd44](https://github.com/Entif-AI/Bilqis-MLX/commit/4c1bd44abc3ea04c862e3318c5428e9f832bc654))
* **operator:** classify lesson capacity drift correctly ([7da6330](https://github.com/Entif-AI/Bilqis-MLX/commit/7da6330febcdacd100b5252800ba5dc93822cfd4))
* **operator:** make ctrl-c shutdown graceful ([2ed3d81](https://github.com/Entif-AI/Bilqis-MLX/commit/2ed3d81762c42129de9b1ececd76412ab8f03b12))
* **qualification:** require complete source assessment before promotion ([836aa5e](https://github.com/Entif-AI/Bilqis-MLX/commit/836aa5ec3b4a45fc5e2dea35dc9284d8b72df5ab))
* **release:** accept generated changelog headings ([990369f](https://github.com/Entif-AI/Bilqis-MLX/commit/990369ff1248e08bd7d0d6bc192f259e5f1e9a2f))
* **release:** accept generated changelog headings ([324b46d](https://github.com/Entif-AI/Bilqis-MLX/commit/324b46da32c0a996e0059e8fd7dbbb42de079e6a))
* **resume:** bind outbox advancement to durable IDs and verify historical cohort scopes ([20f35a3](https://github.com/Entif-AI/Bilqis-MLX/commit/20f35a33cb7c44ab68e8b5581838fc324291a26c))
* **resume:** preserve distinct v2 assessment evidence strata ([d2dafb8](https://github.com/Entif-AI/Bilqis-MLX/commit/d2dafb87ee70988296d554e743a73394716a7061))
* **resume:** reconcile inherited v1 outbox and historical cohort after v2 cutover ([1eb091b](https://github.com/Entif-AI/Bilqis-MLX/commit/1eb091bdf064876137baeded71464c2dd20f2595))
* **resume:** recover sealed historical curriculum into verified v2 release ([8a28b7b](https://github.com/Entif-AI/Bilqis-MLX/commit/8a28b7b8fa3556275d94bcb4c2f8b7dbdc217c1b))
* **resume:** repair scope-rubric evidence drift ([e8616ea](https://github.com/Entif-AI/Bilqis-MLX/commit/e8616ea1e38152db65c52c34db3f1826e3cba8ec))
* **retention:** accept absent active-grade frontier evidence ([759e9b6](https://github.com/Entif-AI/Bilqis-MLX/commit/759e9b661b7470f06a45835bb2efd8ca33d3e5e1))
* **retention:** align teaching with fresh transfer ([39db37f](https://github.com/Entif-AI/Bilqis-MLX/commit/39db37fcc4fc2c7edf44915abd8ed527a733e58e))
* **retention:** protect developmental frontier during debt visits ([e1c74b2](https://github.com/Entif-AI/Bilqis-MLX/commit/e1c74b22c2ce9cbb865c4a16d25296dd9c5a57f7))
* **retention:** reenter deferred mastery debt ([8f29ec3](https://github.com/Entif-AI/Bilqis-MLX/commit/8f29ec39decd64994cd95b690babbace87891a4b))
* **retention:** respect zero weakness replay capacity ([a0970f7](https://github.com/Entif-AI/Bilqis-MLX/commit/a0970f7c8663d298a971d3af03018f664e51630e))
* **retention:** scale protected loss budgets to evidence ([9720439](https://github.com/Entif-AI/Bilqis-MLX/commit/9720439c6864cdc092b811d0f97f90de5273a9c0))
* **retention:** scale protected loss budgets to evidence ([56254b6](https://github.com/Entif-AI/Bilqis-MLX/commit/56254b679e3da06e28fecdd9d95dab660430c55f))
* **retention:** support direct U7C fragile replay ([d0ca5e2](https://github.com/Entif-AI/Bilqis-MLX/commit/d0ca5e21fd1b4601690b1e664306b227f7e97954))
* **retention:** tolerate fully withheld active grade ([09a5191](https://github.com/Entif-AI/Bilqis-MLX/commit/09a519153fab38c391dcb626e686de43f103e268))
* **runtime:** complete executable rubric migration and diagnostic readback ([4c74f50](https://github.com/Entif-AI/Bilqis-MLX/commit/4c74f50cf47a2b057e5a357b63dec9d113104f7e))
* **runtime:** disable runaway MLX training cache ([b5bb508](https://github.com/Entif-AI/Bilqis-MLX/commit/b5bb508f10f1077ea29a348c070233c9b4ddd8c1))
* **runtime:** integrate main recovery and frontier scheduling ([c4e9abb](https://github.com/Entif-AI/Bilqis-MLX/commit/c4e9abb1333ee45cb3def230f3801fb8e1c0a17c))
* **runtime:** keep release migration independent of neural dependencies ([090a347](https://github.com/Entif-AI/Bilqis-MLX/commit/090a347e8eda575c49cdfb27aa0f1e4d765d7443))
* **runtime:** preserve experiment custody across retained boundaries ([bcb828f](https://github.com/Entif-AI/Bilqis-MLX/commit/bcb828f9050f01f03e2d9019e3e57fd352d8f407))
* **runtime:** restore bounded soup retention ([0640964](https://github.com/Entif-AI/Bilqis-MLX/commit/06409643583a2fe1021eaa9af64c1cf6af559882))
* **runtime:** stop pinning archived soup tensors ([6574116](https://github.com/Entif-AI/Bilqis-MLX/commit/65741163202850a119e52c350b0b48411c8ec132))
* **scheduler:** cap nongating B debt at twenty percent ([d89b139](https://github.com/Entif-AI/Bilqis-MLX/commit/d89b13961a43984867f135a1690949dc0d18ee17))
* **scheduler:** give Grade B bounded full runs ([d22564d](https://github.com/Entif-AI/Bilqis-MLX/commit/d22564d6a9dd2f4293bfa297abdc9a98f92099b5))
* **scheduler:** preserve cumulative scope on grade replay ([639441f](https://github.com/Entif-AI/Bilqis-MLX/commit/639441fd37ef003966bf67c76149d2ed8321e4aa))
* **scheduler:** verify cumulative rubric through quarantine ([3896b98](https://github.com/Entif-AI/Bilqis-MLX/commit/3896b98043a7254c74ad2bcd1d92c01043a0c803))
* **school:** accept promotion-sweep stagnation visits ([8fc4837](https://github.com/Entif-AI/Bilqis-MLX/commit/8fc483705ad53f15aa83693f6a057361c1c4cb75))
* **school:** bind promotion retries to learning state ([d89bc02](https://github.com/Entif-AI/Bilqis-MLX/commit/d89bc0275760ec5720bd35dffc716d8461eddec5))
* **school:** recover between grade sweeps ([2b53bfd](https://github.com/Entif-AI/Bilqis-MLX/commit/2b53bfd4d63297142b149017dd6332c2accff032))
* **school:** restore blocked debt liveness ([efcb7df](https://github.com/Entif-AI/Bilqis-MLX/commit/efcb7df574b3401f23a8e5412ede874543d283d6))
* **school:** restore bounded cross-grade spiral ([136f1d2](https://github.com/Entif-AI/Bilqis-MLX/commit/136f1d2feb849848933f5e560677df8f63ccf99b))
* **school:** teach grade B without stagnation quarantine ([c9fdb54](https://github.com/Entif-AI/Bilqis-MLX/commit/c9fdb542afd00922bfb9ea2c0d8b1756558bd8a4))
* **skos:** anchor senses to source coordinates instead of gloss hashes ([be6f671](https://github.com/Entif-AI/Bilqis-MLX/commit/be6f6711af0b91df258eabad7b6497f27d763e5a))
* **skos:** correct Chapter 3 source accounting ([4380f40](https://github.com/Entif-AI/Bilqis-MLX/commit/4380f4036c3c4d49a09ddad080906194346cb957))
* **skos:** page reset ownership scans and bound atomic reset memory ([58955da](https://github.com/Entif-AI/Bilqis-MLX/commit/58955da182f0c05401c676f5a7266b41235431c0))
* **skos:** preserve raw coverage beside gate evidence ([#72](https://github.com/Entif-AI/Bilqis-MLX/issues/72)) ([d97b5ab](https://github.com/Entif-AI/Bilqis-MLX/commit/d97b5ab6bc451287538ba30924d7d584a4c1e13b))
* **skos:** require the complete registered semantic smoke suite ([#77](https://github.com/Entif-AI/Bilqis-MLX/issues/77)) ([818b11b](https://github.com/Entif-AI/Bilqis-MLX/commit/818b11b3dab2ba2c34e4cf36fe6b47b43f8110c5))
* **skos:** retain mapping support in conformance evidence ([#72](https://github.com/Entif-AI/Bilqis-MLX/issues/72)) ([6d2b220](https://github.com/Entif-AI/Bilqis-MLX/commit/6d2b2204168e4151c12e15abf1e3e212f2f8ab2c))
* **source:** prevent composite identity collisions ([8a0c19b](https://github.com/Entif-AI/Bilqis-MLX/commit/8a0c19b39c3298c1ca6e1327686134c546657f10))
* **stagnation:** reconcile scope across grade transitions ([e7ef5b6](https://github.com/Entif-AI/Bilqis-MLX/commit/e7ef5b6d5a86249b113ca388e1b634f3ae494607))
* **state:** read experiment and dashboard receipts through DAG owner ([16bf33e](https://github.com/Entif-AI/Bilqis-MLX/commit/16bf33e8f92ea364a10a4689d738b8373d24ef13))
* **state:** replay identical Merkle generations without reparenting ([4b44cc3](https://github.com/Entif-AI/Bilqis-MLX/commit/4b44cc30d7ba386ce5ebe352073220b7f07e72f6))
* **state:** retain migrated-head publication on idempotent retries ([94c2e50](https://github.com/Entif-AI/Bilqis-MLX/commit/94c2e500523b45472ee257cf4021730309f5b848))
* **storage:** align custody warming with live soup roots ([724c7eb](https://github.com/Entif-AI/Bilqis-MLX/commit/724c7eb80f8478a6758685345127a37487eaf2c9))
* **storage:** inspect logical DAG state ([8c9897b](https://github.com/Entif-AI/Bilqis-MLX/commit/8c9897b5628cd26c333feacd62c84d5d385401a8))
* **storage:** inspect logical DAG state ([79f3aef](https://github.com/Entif-AI/Bilqis-MLX/commit/79f3aefc881fe943b40067764202e1ed0e08e7e9))
* **storage:** keep custody warming below trainer layer ([84051bf](https://github.com/Entif-AI/Bilqis-MLX/commit/84051bf1b1da24966f6da7f9b3f1c7039bb5b2d1))
* **storage:** keep custody warming below trainer layer ([7fac921](https://github.com/Entif-AI/Bilqis-MLX/commit/7fac9218a9a76fe36e72fa24138b457a2c85af66))
* **storage:** type data-plane invariants ([815f76e](https://github.com/Entif-AI/Bilqis-MLX/commit/815f76e9eb16ee27b8e3501805b4ac9c4f24c9ee))
* **storage:** type data-plane invariants ([385296d](https://github.com/Entif-AI/Bilqis-MLX/commit/385296dbc566250193e0dced4e10a7e263169f5a))
* **teacher:** adapt candidate horizon under retention pressure ([e60eaee](https://github.com/Entif-AI/Bilqis-MLX/commit/e60eaee5273c92b25c5f53932bebd522d5075a83))
* **teacher:** aggregate stagnation at capability scope ([6f1cd64](https://github.com/Entif-AI/Bilqis-MLX/commit/6f1cd649106297a0e03f58db8d4bbf1b2c3d6e02))
* **teacher:** bound active strategies and promotion floor ([08094eb](https://github.com/Entif-AI/Bilqis-MLX/commit/08094eb3e7e93621d8fb99b8246f926c8f3ffbf9))
* **teacher:** calibrate shadow stopping horizon ([96e0ba0](https://github.com/Entif-AI/Bilqis-MLX/commit/96e0ba046d784d8d47b9f84a13b4d898fe469350))
* **teacher:** collapse ineffective preview variants ([1dc20b5](https://github.com/Entif-AI/Bilqis-MLX/commit/1dc20b52d200132dd38ee40cb2177e1bee579637))
* **teacher:** condition strategy selection on diagnostics ([e42a8f4](https://github.com/Entif-AI/Bilqis-MLX/commit/e42a8f474fce88f0f0accd8e7fb339a6f2ec19b8))
* **teacher:** credit realized lesson delivery ([9662bd6](https://github.com/Entif-AI/Bilqis-MLX/commit/9662bd6d7cb912db21a5bd26c19d027921dc4d3c))
* **teacher:** dedupe champion weakness identities ([c93ab7a](https://github.com/Entif-AI/Bilqis-MLX/commit/c93ab7a21908d37e53ee6a0af4d2eda71420319d))
* **teacher:** dedupe semantic miss replay ([d4fdb8e](https://github.com/Entif-AI/Bilqis-MLX/commit/d4fdb8e1f18053783e3c7e389696382410c120e1))
* **teacher:** demote repeated no-gain strategies ([0be357e](https://github.com/Entif-AI/Bilqis-MLX/commit/0be357e1d5582d3df4eee652a0b51952f440dcff))
* **teacher:** demote repeated no-gain strategies ([0f966d9](https://github.com/Entif-AI/Bilqis-MLX/commit/0f966d9a5ccf4504c6a82af55fb96f38157cd98c))
* **teacher:** distinguish learner-state regions ([bb7a5ed](https://github.com/Entif-AI/Bilqis-MLX/commit/bb7a5ed14739ae21ef2a41393c69e0ec5b765204))
* **teacher:** distinguish target inertia from interference ([4246f95](https://github.com/Entif-AI/Bilqis-MLX/commit/4246f95062c891fb6412854cd89ea4c8b7a0303f))
* **teacher:** escape rejection-only novelty loops ([200023f](https://github.com/Entif-AI/Bilqis-MLX/commit/200023fd17dfa226d96b1646c80f4cdb87752021))
* **teacher:** exploit retained contextual winners immediately ([ccac889](https://github.com/Entif-AI/Bilqis-MLX/commit/ccac8899dd1210617066cb41cb5e20a115edbde8))
* **teacher:** exploit retained strategy evidence ([13e5252](https://github.com/Entif-AI/Bilqis-MLX/commit/13e525215549e4a2ba0d1e48f4842a89e945ed35))
* **teacher:** handle fresh active strategy bench ([31389c3](https://github.com/Entif-AI/Bilqis-MLX/commit/31389c35f9c2746112925194f9904ac3fcf595f3))
* **teacher:** import shadow rung scheduler ([ddf21e7](https://github.com/Entif-AI/Bilqis-MLX/commit/ddf21e79341bdbd4a587b49250165d8d70c6c225))
* **teacher:** pool learning-rate evidence under pressure ([706ef87](https://github.com/Entif-AI/Bilqis-MLX/commit/706ef873676ba60c98c5ea2a07daca3e6f12ecec))
* **teacher:** prioritize champion-correct student misses ([62b65e1](https://github.com/Entif-AI/Bilqis-MLX/commit/62b65e190f85814767e63796a359c76ffce41c7e))
* **teacher:** reset stale geometry pressure ([3c59208](https://github.com/Entif-AI/Bilqis-MLX/commit/3c59208c05a0a30d57d6077dc954896492aed993))
* **teacher:** retire stale same-student policies ([7ca5b08](https://github.com/Entif-AI/Bilqis-MLX/commit/7ca5b0858edf6a83bd7f1a60e9e0ab02cae20592))
* **teacher:** rotate rejected teaching evidence ([fa52630](https://github.com/Entif-AI/Bilqis-MLX/commit/fa5263087095d41cd2ac9e6d7e3b5dc733cb7ecd))
* **teacher:** scale repeated no-gain selection debt ([1ab1ba7](https://github.com/Entif-AI/Bilqis-MLX/commit/1ab1ba766e120fd7558355e7a437dc8fc757dd67))
* **telemetry:** bind exam scope to scored inventory ([a8e55eb](https://github.com/Entif-AI/Bilqis-MLX/commit/a8e55ebd29cda1746290b334b4f7923930ae5ad7))
* **telemetry:** expose capability-best checkpoint saves ([ae31d98](https://github.com/Entif-AI/Bilqis-MLX/commit/ae31d98667c8ae34ea94b6e9bffd46d9fdbc2712))
* **telemetry:** key live exams by assessment scope ([10bc861](https://github.com/Entif-AI/Bilqis-MLX/commit/10bc86119a46be299b2f4325bf9254aac5188e92))
* **trainer:** add B stagnation grace ([d367df1](https://github.com/Entif-AI/Bilqis-MLX/commit/d367df1ebf55e402543d2faa6205297fb43a7acf))
* **trainer:** carry mastery debt and batch title defense ([d3a13e0](https://github.com/Entif-AI/Bilqis-MLX/commit/d3a13e0604cb19f7bc3225d3db97f769a0739179))
* **trainer:** cover binary truth patterns ([283050e](https://github.com/Entif-AI/Bilqis-MLX/commit/283050e17154bf317c8eadefa1f17d55cfd13f00))
* **trainer:** defer unmeasured championship work ([75a172b](https://github.com/Entif-AI/Bilqis-MLX/commit/75a172b9b24959701d22b2656419a1fe5351ca55))
* **trainer:** keep flash mode in grade spiral ([e22a7d2](https://github.com/Entif-AI/Bilqis-MLX/commit/e22a7d276e9497b4dfb2cbfba6d8a9ab858f33ea))
* **trainer:** make timing trace write ahead ([96a65ba](https://github.com/Entif-AI/Bilqis-MLX/commit/96a65ba62e8567b28e89765dee9c52752db3f940))
* **trainer:** measure fresh debt admission boundary ([72b67b4](https://github.com/Entif-AI/Bilqis-MLX/commit/72b67b484075c302cda913c811b306872e11aa50))
* **trainer:** preserve frontier custody across grade growth ([4888683](https://github.com/Entif-AI/Bilqis-MLX/commit/48886837674133ebef0ebb244fe7c73def4c720c))
* **trainer:** preserve promotion sweep capacity ([5c5a0ec](https://github.com/Entif-AI/Bilqis-MLX/commit/5c5a0ec7f62db2fcd13a0873d2ee95e6cad19938))
* **trainer:** protect preservation from miss replay ([2987e7b](https://github.com/Entif-AI/Bilqis-MLX/commit/2987e7b9de71adf440a9e26b75041077824ce667))
* **trainer:** rehabilitate sole-grade mastery debt ([ade1a53](https://github.com/Entif-AI/Bilqis-MLX/commit/ade1a5398548f252ceb1f6acb1bb7f2b6dd182c4))
* **trainer:** restore fresh evals and contain stagnation ([a041b01](https://github.com/Entif-AI/Bilqis-MLX/commit/a041b0181fd8a1e8d2d0b953fd5e79ee72f6c88b))
* **trainer:** validate typed live exam factors ([61b942f](https://github.com/Entif-AI/Bilqis-MLX/commit/61b942f00b1adad5e3994316b032e6183e816e5b))
* **train:** execute admitted v2 source contracts on live resume ([3d8bf5c](https://github.com/Entif-AI/Bilqis-MLX/commit/3d8bf5c676d696accc902536f71a0808e99252e2))
* **training:** continue through staged stagnation debt ([c9cc80c](https://github.com/Entif-AI/Bilqis-MLX/commit/c9cc80cd35060d25abe83c2f49d2fa39ad8fcff4))
* **training:** continue through staged stagnation debt til bout tree fiddy ([2327c42](https://github.com/Entif-AI/Bilqis-MLX/commit/2327c42f323d10f4444b2c3932e4bdacc15b29e0))
* **training:** require sustained no-progress before stagnation ([e4cc1a3](https://github.com/Entif-AI/Bilqis-MLX/commit/e4cc1a36449a02c8aaada3822aa1b4b0fc339ab7))
* **train:** survive stale exam frontiers and post-evaluation quarantine ([1c205d2](https://github.com/Entif-AI/Bilqis-MLX/commit/1c205d24f392669b9e7f0c4eb6402095930d8977))
* **ui:** bound mastery top to score eras ([f9ab4ef](https://github.com/Entif-AI/Bilqis-MLX/commit/f9ab4ef7d66705200d23509b16caf39e5dd1e178))
* **ui:** keep TOP label in mastery scores ([ba07fa4](https://github.com/Entif-AI/Bilqis-MLX/commit/ba07fa40192c0aa3c665e215c196787867d5c68c))
* **ui:** restore dashboard score column width ([314dc8b](https://github.com/Entif-AI/Bilqis-MLX/commit/314dc8b61994ed19f9e7b8e4ffc38a224cb54919))
* verify predecessor v2 cohort custody ([24771da](https://github.com/Entif-AI/Bilqis-MLX/commit/24771dad34ae95ea82915b67ee0ce9c714b41eed))
* **visits:** big money salvia ([eb82c9a](https://github.com/Entif-AI/Bilqis-MLX/commit/eb82c9a1d14e58d83bd7969c41469f57d2bf1253))


### Performance Improvements

* **ci:** make mature SKOS verification content-addressed ([0405f13](https://github.com/Entif-AI/Bilqis-MLX/commit/0405f139b15c19ba3f21e48821c94cfbfc370da5))
* **ci:** skip unchanged SKOS release proofs ([6c9047f](https://github.com/Entif-AI/Bilqis-MLX/commit/6c9047fa7abe78b375e99e51d7909bc3f7372727))
* **curriculum:** cache numeric miss scope requirements ([788022b](https://github.com/Entif-AI/Bilqis-MLX/commit/788022beb2da0eea41321f64ddbf72698b1f48d8))
* **diagnostics:** preselect comparable exam history ([4cbf157](https://github.com/Entif-AI/Bilqis-MLX/commit/4cbf157436aea941ce061891c7a7bd06c14ff293))
* **events:** index append-only ledger ([2dcb06f](https://github.com/Entif-AI/Bilqis-MLX/commit/2dcb06f5680671a630e1e33bc5567a2c977236b1))
* **events:** index append-only ledger ([ee5aa46](https://github.com/Entif-AI/Bilqis-MLX/commit/ee5aa46344198e0f57d00a751e5b85cd0c724812))
* **merkle-dag:** dat girl scout was bout 8 stories tall an a giant crustacean from da paleolithic era ([025bca5](https://github.com/Entif-AI/Bilqis-MLX/commit/025bca51c78509acd0b1b898f16e9fcf84d25941))
* **mlx:** batch short-row inference adaptively ([94179d1](https://github.com/Entif-AI/Bilqis-MLX/commit/94179d1b7384314805cac2fce67a5ac2162e2726))
* **runtime:** stop copying full receipt on every visit ([59df3a3](https://github.com/Entif-AI/Bilqis-MLX/commit/59df3a339f3603106b29566ed0cdb8d4bb532597))
* **state:** move school receipts to shared Merkle data plane ([04e3978](https://github.com/Entif-AI/Bilqis-MLX/commit/04e3978190c602586167e997e717fdf909c28cac))
* **state:** move school receipts to shared Merkle data plane ([69c5312](https://github.com/Entif-AI/Bilqis-MLX/commit/69c5312c4f0bcb7b4f104914ce82de2e699e7ea4))
* **state:** shard teacher contexts ([0463904](https://github.com/Entif-AI/Bilqis-MLX/commit/0463904c08bf971adf1e1c7e271d1cfc0e79196f))
* **state:** shard teacher contexts ([eb8e119](https://github.com/Entif-AI/Bilqis-MLX/commit/eb8e119e48441bd981f304cf9a445a51c9e5de71))
* **storage:** keep cold state off hot path ([6d773d1](https://github.com/Entif-AI/Bilqis-MLX/commit/6d773d11dd8ca55239b1ca4c47153b55ca68a7ec))
* **storage:** keep cold state off hot path ([dce76e6](https://github.com/Entif-AI/Bilqis-MLX/commit/dce76e6baa0335bd0d6418b535c6dd0f06b2e7ce))
* **storage:** share hardlink digest proofs ([d098acb](https://github.com/Entif-AI/Bilqis-MLX/commit/d098acb5dff533b09d6dab175e3f282ac778a01c))
* **storage:** share hardlink digest proofs ([4140e05](https://github.com/Entif-AI/Bilqis-MLX/commit/4140e051c0edd11d57925397ac070a0b0f6a59f8))
* **trainer:** add three-lane source prefetch ([bfe172a](https://github.com/Entif-AI/Bilqis-MLX/commit/bfe172a0daa18d8c9f844b13bb6a6cef76727cc2))

## [0.5.0] - 2026-10-26

### Added
- Immutable retained-learning qualification manifests, evidence-bound preflight and explicit human launch for two controlled topology arms.
- Fresh seeded initialization, frozen prerequisite-compatible workload prefixes, finite visit budgets and independently seeded post-acquisition/fresh-probe receipts.

## [0.4.0] - 2026-10-26

### Added
- Replayable Factory teacher observations with ordered delivery sidecars, explicit measurement missingness, topology/policy partitions and canonical checkpoint-outbox joins.
- Read-only reconstruction and diagnostic summaries, without changing teacher selection, source draws, candidate horizons or retention authority.

## [0.3.0] - 2026-10-26

### Added
- Typed, versioned structural model topology selected at run creation, recorded with run/checkpoint identity and verified on resume independently of semantic vocabulary growth.
- Deterministic disposable non-default model construction with explicit initialization provenance; historical defaults retain their imported student and own AdamW.

## [0.2.0] - 2026-10-17

### Added
- One canonical `bilqis-mlx` source checkout with pinned, locally vendored historical source oracles, teacher policy and the original bootstrap checkpoint kept out of Git.
- Whole-student, own-AdamW retention peaks across comparable curriculum cohorts and a tighter recovery-stage harmful-candidate gate.
- Configurable ignored `BILQIS_STORAGE_ROOT`, with retained checkpoint bundles and human-operated resume.
- Source-grounded Grade C numeric staircase, typed mentor soups, contextual teacher outcomes and append-only semantic registry growth.
- Reproducible, checksum-verified state lineage migration; bounded, lossless JSON generation compaction at normal stop boundaries.
- Release metadata, Conventional Commit validation, change recording and gated automation adapted from the reference Bilqis repo.

### Fixed
- Frozen soups partition incompatible historical vocabulary generations rather than averaging differently shaped tensors.
- Actual vocabulary metadata now follows the admitted semantic graph while protecting the immutable historical token prefix.
- Finder-generated `.DS_Store` files no longer interrupt checkpoint custody; unknown files and symlinks still block retirement.
- Resume repairs retain the original model and optimizer and do not mistake a provisional retention gate pass for graduation.

### Retained
- Existing complete student and native AdamW optimizer, historical teachers/champions and their provenance, original source-checkpoint SHA, preserved curriculum rubrics and all verified historical state before any archive retirement.
- Strict human ownership of actual training. No new neural runs are started by CI, tests or migration helpers.

### Limitations
- Whole-student retention peaks are historical custody references, not automatic student rollback or independently proven long-term protection.
- Old worktrees and prior checkpoints remain as recovery copies until independently verified external archival is possible.
- MLX-specific neural functionality requires Apple Silicon; portable CI does not assert that GitHub's Linux workers trained a student.
