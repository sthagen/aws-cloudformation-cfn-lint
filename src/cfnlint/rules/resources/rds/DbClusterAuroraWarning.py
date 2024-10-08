"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: MIT-0
"""

from __future__ import annotations

from typing import Any

import cfnlint.data.schemas.extensions.aws_rds_dbcluster
from cfnlint.jsonschema import ValidationResult, Validator
from cfnlint.rules.jsonschema.CfnLintJsonSchema import CfnLintJsonSchema, SchemaDetails


class DbClusterAuroraWarning(CfnLintJsonSchema):
    id = "W3693"
    shortdesc = "Validate Aurora DB cluster configuration for ignored properties"
    description = (
        "When creating an Aurora DB Cluster there are fields that "
        "will allow for successful deployment but are ignored"
    )
    tags = ["resources"]
    source_url = "https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-rds-dbcluster.html#cfn-rds-dbcluster-engineversion"

    def __init__(self) -> None:
        super().__init__(
            keywords=["Resources/AWS::RDS::DBCluster/Properties"],
            schema_details=SchemaDetails(
                module=cfnlint.data.schemas.extensions.aws_rds_dbcluster,
                filename="aurora_warning.json",
            ),
            all_matches=True,
        )

    def validate(
        self, validator: Validator, keywords: Any, instance: Any, schema: dict[str, Any]
    ) -> ValidationResult:
        for err in super().validate(validator, keywords, instance, schema):
            if err.schema is False:
                err.message = (
                    "Additional properties are not allowed "
                    f"{err.path[0]!r} when creating Aurora cluster"
                )

            yield err
