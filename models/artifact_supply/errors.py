from __future__ import annotations


class ArtifactSupplyError(RuntimeError):
    """Base fail-closed model supply error."""


class ManifestError(ArtifactSupplyError):
    pass


class TermsNotAdmitted(ArtifactSupplyError):
    pass


class IntegrityError(ArtifactSupplyError):
    pass


class CompatibilityError(ArtifactSupplyError):
    pass


class DowngradeError(ArtifactSupplyError):
    pass


class ActivationInterrupted(ArtifactSupplyError):
    pass
