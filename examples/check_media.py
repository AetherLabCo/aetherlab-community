"""Check an image against guardrail policies with scalar MediaGuard.

`check_media` accepts a file path/bytes (input_type="file"), an HTTPS URL
(input_type="url"), or a base64 string (input_type="base64"). Base64 is
supported only on this scalar endpoint, not in batches.
"""

from aetherlab import AetherLabClient


def main() -> None:
    with AetherLabClient() as client:
        result = client.check_media(
            "https://raw.githubusercontent.com/github/explore/main/topics/python/python.png",
            input_type="url",
            blacklisted_keywords=["violence"],
            reasoning_mode="low",
        )
        print(result.compliance_status)  # "Compliant" or "Non-Compliant"
        print(result.avg_threat_level)
        print(result.rationale)


if __name__ == "__main__":
    main()
