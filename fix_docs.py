"""Patch RTM.md and DESIGN.md to reflect matric login and 6 services."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def patch_rtm():
    p = ROOT / "docs" / "RTM.md"
    s = p.read_text(encoding="utf-8")

    # FR-04: login with email -> login with matric
    s = s.replace(
        "| **FR-04** | Login with email + password |",
        "| **FR-04** | Login with matric / staff number + password |",
    )

    # FR-01: emphasize matric is required
    s = s.replace(
        "| **FR-01** | Register with email/password/name/role/matric |",
        "| **FR-01** | Bootstrap-only registration: first user becomes admin; requires email, password, matric, name, role |",
    )

    # NFR-01: email lookup -> matric lookup
    s = s.replace(
        "indexed email lookup",
        "indexed matric lookup",
    )

    # FR-02: keep email but add matric
    s = s.replace(
        "| **FR-02** | Reject duplicate email |",
        "| **FR-02** | Reject duplicate email OR duplicate matric |",
    )

    p.write_text(s, encoding="utf-8", newline="\n")
    print(f"Patched: {p}")


def patch_design():
    p = ROOT / "docs" / "DESIGN.md"
    s = p.read_text(encoding="utf-8")

    # Replace "three independent mock services" (2 occurrences)
    s = s.replace(
        "three independent mock services",
        "six independent mock services",
    )
    s = s.replace(
        "Three independent mock services",
        "Six independent mock services",
    )

    # Replace "three independent mock services (Portal, LMS, Library)"
    s = s.replace(
        "six independent mock services (Portal, LMS, Library)",
        "six independent mock services (Portal, LMS, Library, Hostel, Wi-Fi, Result Checker)",
    )

    # Rubric line at 329
    s = s.replace(
        '| "distributed/service-oriented solution" | Three independent services\non distinct ports, each a separate OS process |',
        '| "distributed/service-oriented solution" | Six independent services\non distinct ports, each a separate OS process |',
    )

    p.write_text(s, encoding="utf-8", newline="\n")
    print(f"Patched: {p}")


if __name__ == "__main__":
    patch_rtm()
    patch_design()
    print("All patches applied.")