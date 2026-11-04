# Versioning and releases

The toolkit uses semantic version tags in the form `vMAJOR.MINOR.PATCH`. A major version may break workflow inputs, outputs, or behavior; a minor version adds backwards-compatible capabilities; a patch fixes defects without changing the supported interface. Maintain a changelog entry for each release, call out required permissions and migration steps, and use GitHub-generated release notes as supplemental context.

Reusable workflows should be referenced with a published protected version tag such as `@v1.2.0`, or a reviewed full commit SHA. Document the source commit represented by each selected tag/SHA in the consumer's change record. Do not reference `main` or another mutable branch. Protect `v*` tags with a GitHub ruleset that limits creation/update to release maintainers; a semver-shaped tag alone is not immutable. A security fix should be released promptly and consumers should update their pinned version or SHA through normal review.

Before creating a release:

1. Run the local config/workflow validation and unit suite.
2. Review the workflow diff, especially permission changes and external action pins.
3. Update documentation and changelog notes, including migration requirements.
4. Merge the reviewed change, then create a protected `vMAJOR.MINOR.PATCH` tag at that commit.
5. Confirm the GitHub Release and attached manifest identify the intended commit.

Consumers should upgrade in a test repository first, verify the run and permission requirements, then roll the release through projects. Record the prior and new ref, caller workflow diff, CI run URL, changed inputs/permissions, and rollback ref. For breaking changes, maintain the prior major workflow for an announced support window where practical and provide a migration guide. If a pinned release is vulnerable, stop new use immediately, publish a fixed release, and notify consumers through the project's normal advisory channel. Reusable workflow tags and examples do not mean a release has been published; verify the tag and manifest before adoption.
