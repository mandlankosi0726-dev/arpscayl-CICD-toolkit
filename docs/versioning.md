# Versioning and releases

The toolkit uses semantic version tags in the form `vMAJOR.MINOR.PATCH`. A major version may break workflow inputs, outputs, or behavior; a minor version adds backwards-compatible capabilities; a patch fixes defects without changing the supported interface. Maintain a changelog entry for each release, call out required permissions and migration steps, and use GitHub-generated release notes as supplemental context.

Reusable workflows should be referenced with a published version tag such as `@v1.2.0`. Pin to a reviewed full commit SHA when a consumer needs stronger immutability, and document the release represented by that SHA. Do not permanently reference `main` or another mutable branch. A security fix should be released promptly and consumers should update their pinned version or SHA through normal review.

Before creating a release:

1. Run the local config/workflow validation and unit suite.
2. Review the workflow diff, especially permission changes and external action pins.
3. Update documentation and changelog notes, including migration requirements.
4. Merge the reviewed change, then create a protected `vMAJOR.MINOR.PATCH` tag at that commit.
5. Confirm the GitHub Release and attached manifest identify the intended commit.

Consumers should upgrade in a test repository first, verify the run and permission requirements, then roll the release through projects. For breaking changes, maintain the prior major workflow for an announced support window where practical and provide a migration guide. If a pinned release is vulnerable, stop new use immediately, publish a fixed release, and notify consumers through the project's normal advisory channel.
