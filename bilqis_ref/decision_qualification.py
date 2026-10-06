"""Grade frozen primary profiles; raw-temperature diagnostics cannot earn admission."""


def classify(profiles, policy, *, runtime_stable=True, source_permitted=True, environment_ready=True):
    if not source_permitted:return 'BLOCKED_SOURCE_POLICY'
    if not environment_ready:return 'BLOCKED_ENVIRONMENT'
    if not runtime_stable:return 'RUNTIME_UNSTABLE'
    primary={name:profiles[name] for name in ('K1','S1') if name in profiles}
    if len(primary)!=2 or any(p['labeled']<policy['qualification_min_labeled'] for p in primary.values()):
        return 'ENGINEERING_READY_QUALITY_UNCLEAR'
    qualified={name for name,p in primary.items() if p['accuracy'] is not None
               and p['accuracy']>=policy['qualification_accuracy'] and p['confident_wrong']==0
               and p['false_confident_local_completions']==0}
    if qualified=={'K1','S1'}:return 'QUALIFIED_BOTH'
    if 'K1' in qualified:return 'QUALIFIED_KEV4'
    if 'S1' in qualified:return 'QUALIFIED_SEMIF'
    return 'QUALITY_INADEQUATE'
