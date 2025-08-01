"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: MIT-0
"""

from collections import deque

import pytest

from cfnlint.context.context import Transforms
from cfnlint.jsonschema import CfnTemplateValidator, ValidationError
from cfnlint.rules.functions.Ref import Ref
from cfnlint.rules.functions.ToJsonString import ToJsonString
from cfnlint.template import Template


@pytest.fixture(scope="module")
def rule():
    rule = ToJsonString()
    yield rule


@pytest.fixture(scope="module")
def cfn():
    return Template(
        "",
        {"Resources": {"MyResource": {"Type": "AWS::S3::Bucket"}}},
        regions=["us-east-1"],
    )


@pytest.mark.parametrize(
    "name,instance,schema,context_evolve,expected",
    [
        (
            "Fn::ToJsonString is not supported",
            {"Fn::ToJsonString": []},
            {"type": "string"},
            {},
            [
                ValidationError(
                    "Fn::ToJsonString is not supported without "
                    "'AWS::LanguageExtensions' transform",
                    path=deque([]),
                    schema_path=deque([]),
                    validator="fn_tojsonstring",
                    rule=ToJsonString(),
                ),
            ],
        ),
        (
            "Fn::ToJsonString is invalid with wrong output type",
            {"Fn::ToJsonString": {"foo": "bar"}},
            {"type": "object"},
            {"transforms": Transforms(["AWS::LanguageExtensions"])},
            [
                ValidationError(
                    "{'Fn::ToJsonString': {'foo': 'bar'}} is not of type 'object'",
                    path=deque([]),
                    schema_path=deque([]),
                    validator="fn_tojsonstring",
                    rule=ToJsonString(),
                ),
            ],
        ),
        (
            "Fn::ToJsonString is valid with a simple key/value",
            {"Fn::ToJsonString": {"foo": "bar"}},
            {"type": "string"},
            {"transforms": Transforms(["AWS::LanguageExtensions"])},
            [],
        ),
        (
            "Fn::ToJsonString is invalid with an empty object",
            {"Fn::ToJsonString": {}},
            {"type": "string"},
            {"transforms": Transforms(["AWS::LanguageExtensions"])},
            [
                ValidationError(
                    "expected minimum property count: 1, found: 0",
                    path=deque(["Fn::ToJsonString"]),
                    schema_path=deque(["cfnContext", "schema", "minProperties"]),
                    validator="fn_tojsonstring",
                    rule=ToJsonString(),
                ),
            ],
        ),
        (
            "Fn::ToJsonString is invalid with an empty array",
            {"Fn::ToJsonString": []},
            {"type": "string"},
            {"transforms": Transforms(["AWS::LanguageExtensions"])},
            [
                ValidationError(
                    "expected minimum item count: 1, found: 0",
                    path=deque(["Fn::ToJsonString"]),
                    schema_path=deque(["cfnContext", "schema", "minItems"]),
                    validator="fn_tojsonstring",
                    rule=ToJsonString(),
                ),
            ],
        ),
        (
            "Fn::ToJsonString is invalid with a ref to AWS::NotificationARNs",
            {"Fn::ToJsonString": {"Ref": "AWS::NotificationARNs"}},
            {"type": "string"},
            {"transforms": Transforms(["AWS::LanguageExtensions"])},
            [
                ValidationError(
                    "'AWS::NotificationARNs' is not one of "
                    "['MyResource', 'AWS::AccountId', "
                    "'AWS::NoValue', 'AWS::Partition', 'AWS::Region', "
                    "'AWS::StackId', 'AWS::StackName', 'AWS::URLSuffix']",
                    path=deque(["Fn::ToJsonString", "Ref"]),
                    schema_path=deque(
                        [
                            "cfnContext",
                            "schema",
                            "ref",
                            "then",
                            "cfnContext",
                            "schema",
                            "dynamicValidation",
                            "enum",
                        ]
                    ),
                    validator="ref",
                    rule=ToJsonString(),
                ),
            ],
        ),
        (
            "Fn::ToJsonString is valid array with functions",
            {"Fn::ToJsonString": [{"Ref": "MyResource"}]},
            {"type": "string"},
            {"transforms": Transforms(["AWS::LanguageExtensions"])},
            [],
        ),
        (
            "Fn::ToJsonString is valid object with functions",
            {"Fn::ToJsonString": {"Key": {"Ref": "MyResource"}}},
            {"type": "string"},
            {"transforms": Transforms(["AWS::LanguageExtensions"])},
            [],
        ),
    ],
)
def test_validate(name, instance, schema, context_evolve, expected, rule, context, cfn):
    context = context.evolve(**context_evolve)
    validator = CfnTemplateValidator({}).extend(
        validators={
            "ref": Ref().ref,
        }
    )(context=context, cfn=cfn)
    errs = list(rule.fn_tojsonstring(validator, schema, instance, {}))
    assert errs == expected, f"Test {name!r} got {errs!r}"
