from __future__ import annotations


class SkillRuntimeError(RuntimeError):
    pass


class IntegrityError(SkillRuntimeError):
    pass


class PolicyError(SkillRuntimeError):
    pass


class RoutingError(SkillRuntimeError):
    pass


class ReplayError(SkillRuntimeError):
    pass


class SandboxTimeout(SkillRuntimeError):
    pass


class SandboxCrash(SkillRuntimeError):
    pass
