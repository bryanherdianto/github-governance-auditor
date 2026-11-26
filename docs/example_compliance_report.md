# Compliance Report: openai/whisper

- **Repository:** [openai/whisper](https://github.com/openai/whisper)
- **Question:** Run a full compliance assessment across all governance controls.

## Answer

A full compliance assessment across all 5 AI governance controls was completed for openai/whisper. The repository passes 4 controls (Documentation, Licensing, Model Documentation, AI Transparency) and fails 1 control (Security due to missing repository and organization-level security policies).

## Executive Summary

The openai/whisper repository demonstrates strong documentation and open-source practices with a comprehensive README, an approved MIT license, a detailed model card, and clear documentation of intended use and limitations. However, it lacks a dedicated security policy both within the repository and at the organization level.

| Control | Status | Sources |
| --- | --- | --- |
| Documentation | **PASS** | [link](https://github.com/openai/whisper/blob/main/README.md) |
| Licensing | **PASS** | [link](https://github.com/openai/whisper), [link](https://github.com/openai/whisper/blob/main/LICENSE) |
| Model Documentation | **PASS** | [link](https://github.com/openai/whisper/blob/main/model-card.md) |
| AI Transparency | **PASS** | [link](https://github.com/openai/whisper/blob/main/model-card.md) |
| Security | **FAIL** | [link](https://github.com/openai/whisper/tree/main), [link](https://github.com/openai/.github) |

## Detailed Control Evaluations

### Documentation — PASS
**Description:** Does the repository contain a nonempty README file?

**Explanation:** A substantive and non-empty README.md file is present in the repository root.

**Supporting Evidence:**
- Repository contains README.md of size 8246 bytes with substantive content covering overview, setup, available models, command-line usage, and Python usage.

**Source References:**
- https://github.com/openai/whisper/blob/main/README.md

### Licensing — PASS
**Description:** Does the repository use an approved license (MIT or Apache 2.0)?

**Explanation:** The repository uses an approved license, specifically the MIT License, verified via metadata and the LICENSE file.

**Supporting Evidence:**
- Repository metadata specifies license spdx_id as MIT.
- LICENSE file contains standard MIT License text: 'MIT License\n\nCopyright (c) 2022 OpenAI'.

**Source References:**
- https://github.com/openai/whisper
- https://github.com/openai/whisper/blob/main/LICENSE

### Model Documentation — PASS
**Description:** Does the repository contain a model card?

**Explanation:** The repository includes a dedicated model-card.md following Mitchell et al. guidelines.

**Supporting Evidence:**
- Repository contains model-card.md (7307 bytes) titled '# Model Card: Whisper'.

**Source References:**
- https://github.com/openai/whisper/blob/main/model-card.md

### AI Transparency — PASS
**Description:** Are the model's intended use and limitations adequately documented?

**Explanation:** The model card explicitly documents intended use cases, out-of-scope/unintended use cases, and technical limitations.

**Supporting Evidence:**
- model-card.md includes section '## Model Use' detailing evaluated users ('AI researchers studying the robustness, generalization, capabilities, biases, and constraints... useful as an ASR solution for developers') and out-of-scope uses ('caution against using Whisper models to transcribe recordings of individuals taken without their consent or purporting to use these models for any kind of subjective classification').
- model-card.md includes section '## Performance and Limitations' detailing hallucination risks ('predictions may include texts that are not actually spoken in the audio input (i.e. hallucination)'), uneven performance across languages/demographics ('higher word error rate across speakers of different genders, races, ages, or other demographic criteria'), and repetition risks.

**Source References:**
- https://github.com/openai/whisper/blob/main/model-card.md

### Security — FAIL
**Description:** Does the repository contain a security policy?

**Explanation:** Neither repository-level nor organization-level security policy files could be found.

**Supporting Evidence:**
- No SECURITY.md file found in repository root, .github/, or docs/ in file listing.
- check_org_security_policy returned found=false after checking SECURITY.md and .github/SECURITY.md in openai/.github.

**Source References:**
- https://github.com/openai/whisper/tree/main
- https://github.com/openai/.github

**Recommended Remediation:** Add a SECURITY.md file in the root or .github/ folder outlining vulnerability disclosure procedures and contact methods.

## Agent Evidence Collection Trace

- `get_repo_metadata({})` [OK]: Metadata loaded (branch=main, license=MIT).
- `list_repo_files({})` [OK]: Listed 45 paths (total 45).
- `read_repo_file({'path': 'README.md'})` [OK]: Read README.md (8243 chars).
- `read_repo_file({'path': 'LICENSE'})` [OK]: Read LICENSE (1063 chars).
- `read_repo_file({'path': 'model-card.md'})` [OK]: Read model-card.md (7279 chars).
- `check_org_security_policy({})` [OK]: No org-level security policy found.
