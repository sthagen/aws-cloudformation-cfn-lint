"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: MIT-0
"""

from cfnlint._typing import RuleMatches
from cfnlint.helpers import is_function
from cfnlint.rules import CloudFormationLintRule, RuleMatch
from cfnlint.template import Template


class Used(CloudFormationLintRule):
    """Check if Mappings are used anywhere in the template"""

    id = "W7001"
    shortdesc = "Check if Mappings are Used"
    description = "Making sure the mappings defined are used"
    source_url = "https://github.com/aws-cloudformation/cfn-lint"
    tags = ["mappings"]

    def match(self, cfn: Template) -> RuleMatches:
        matches: RuleMatches = []
        findinmap_mappings = []

        mappings = cfn.template.get("Mappings", {})
        k, _ = is_function(mappings)
        if k == "Fn::Transform":
            self.logger.debug(
                f"Mapping Name has a transform. Disabling check {self.id!r}",
            )
            return matches

        if mappings:
            # Get all "FindInMaps" that reference a Mapping
            maptrees = cfn.transform_pre["Fn::FindInMap"]
            for maptree in maptrees:
                if isinstance(maptree[-1], list):
                    map_name = maptree[-1][0]
                    if isinstance(map_name, dict):
                        self.logger.debug(
                            "Mapping Name has a function that can have too many"
                            " variations. Disabling check %s",
                            self.id,
                        )
                        return matches

                    findinmap_mappings.append(maptree[-1][0])
                else:
                    findinmap_mappings.append(maptree[-1])

            # Check if the mappings are used
            for mapname, _ in mappings.items():
                if mapname not in findinmap_mappings:
                    message = "Mapping '{0}' is defined but not used"
                    matches.append(
                        RuleMatch(["Mappings", mapname], message.format(mapname))
                    )

        return matches
