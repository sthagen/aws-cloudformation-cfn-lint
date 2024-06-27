"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: MIT-0
"""

from collections import deque

import pytest

from cfnlint.context.context import Context, Map
from cfnlint.jsonschema import ValidationError
from cfnlint.jsonschema.validators import CfnTemplateValidator


def _resolve(name, instance, expected_results, **kwargs):
    validator = CfnTemplateValidator().evolve(**kwargs)

    resolutions = list(validator.resolve_value(instance))

    for i, (instance, v, errors) in enumerate(resolutions):
        assert instance == expected_results[i][0]
        assert v.context.path.value_path == expected_results[i][1]
        if errors:
            print(errors.validator)
            print(errors.path)
            print(errors.schema_path)
        assert errors == expected_results[i][2]


@pytest.mark.parametrize(
    "name,instance,response",
    [
        (
            "Valid Ref with a single instance",
            {"Ref": {"Ref": "MyResource"}},
            [],
        ),
    ],
)
def test_resolvers_ref(name, instance, response):
    _resolve(name, instance, response)


@pytest.mark.parametrize(
    "name,instance,response",
    [
        (
            "Invalid Ref with an array",
            {"Ref": []},
            [],
        ),
        (
            "Invalid Ref with an invalid object",
            {"Ref": {"foo": "bar"}},
            [],
        ),
        (
            "Invalid Join with an invalid type",
            {"Fn::Join": {"foo": "bar"}},
            [],
        ),
        (
            "Invalid Join with an invalid array length",
            {"Fn::Join": ["a", "b", "c"]},
            [],
        ),
        (
            "Invalid Join with an invalid type for first element",
            {"Fn::Join": [["a"], "b"]},
            [],
        ),
        (
            "Invalid Join with an invalid type for second element",
            {"Fn::Join": ["a", "b"]},
            [],
        ),
        (
            "Invalid Join with an invalid type for second element item",
            {"Fn::Join": ["/", [["a"], "b"]]},
            [],
        ),
        (
            "Invalid Select with an invalid type",
            {"Fn::Select": {"foo": "bar"}},
            [],
        ),
        (
            "Invalid Select with an invalid array length",
            {"Fn::Select": ["a", "b", "c"]},
            [],
        ),
        (
            "Invalid Select with an invalid type for second element",
            {"Fn::Select": ["a", "b"]},
            [],
        ),
        (
            "Invalid Select with an invalid type for second element",
            {"Fn::Select": [0, "b"]},
            [],
        ),
        (
            "Invalid Split with an invalid type",
            {"Fn::Split": {"foo": "bar"}},
            [],
        ),
        (
            "Invalid Split with an invalid array length",
            {"Fn::Split": ["a", "b", "c"]},
            [],
        ),
        (
            "Invalid Split with an invalid type for first element",
            {"Fn::Split": [0, "b"]},
            [],
        ),
        (
            "Invalid Split with an invalid type for second element",
            {"Fn::Split": ["a", ["b"]]},
            [],
        ),
        (
            "Invalid GetAZs with an invalid type ",
            {"Fn::GetAZs": {"a": "b"}},
            [],
        ),
        (
            "Invalid GetAZs with an invalid type ",
            {"Fn::GetAZs": ["a", "b"]},
            [],
        ),
        (
            "Invalid GetAZs with an invalid region",
            {"Fn::GetAZs": "foo"},
            [],
        ),
        (
            "Invalid FindInMap with an invalid type",
            {"Fn::FindInMap": {"foo": "bar"}},
            [],
        ),
        (
            "Invalid FindInMap with an invalid length",
            {"Fn::FindInMap": ["foo", "bar"]},
            [],
        ),
        (
            "Invalid FindInMap with an invalid type for first element",
            {"Fn::FindInMap": [["foo"], "bar", "value"]},
            [],
        ),
        (
            "Invalid FindInMap with an invalid type for second element",
            {"Fn::FindInMap": ["foo", ["bar"], "value"]},
            [],
        ),
        (
            "Invalid FindInMap with an invalid type for third element",
            {"Fn::FindInMap": ["foo", "bar", ["value"]]},
            [],
        ),
        (
            "Invalid FnSub with an invalid type",
            {"Fn::Sub": {"foo": "bar"}},
            [],
        ),
        (
            "Invalid FnSub with an array of wrong length",
            {"Fn::Sub": ["foo", "bar", "value"]},
            [],
        ),
        (
            "Invalid FnSub with the wrong type for element one",
            {"Fn::Sub": [["foo"], {"foo": "bar"}]},
            [],
        ),
        (
            "Invalid FnSub with the wrong type for element two",
            {"Fn::Sub": ["foo", ["bar"]]},
            [],
        ),
    ],
)
def test_invalid_functions(name, instance, response):
    context = Context()
    context.mappings["foo"] = Map({"first": {"second": "bar"}})

    _resolve(name, instance, response, context=context)


@pytest.mark.parametrize(
    "name,instance,response",
    [
        (
            "Valid Join with an empty type",
            {"Fn::Join": [".", []]},
            [],
        ),
        (
            "Valid Join with a list of strings",
            {"Fn::Join": [".", ["a", "b", "c"]]},
            [("a.b.c", deque([]), None)],
        ),
        (
            "Valid GetAZs with empty string",
            {"Fn::GetAZs": ""},
            [
                (
                    [
                        "us-east-1a",
                        "us-east-1b",
                        "us-east-1c",
                        "us-east-1d",
                        "us-east-1e",
                        "us-east-1f",
                    ],
                    deque([]),
                    None,
                )
            ],
        ),
        (
            "Valid FindInMap with a default value",
            {"Fn::FindInMap": ["foo", "bar", "value", {"DefaultValue": "default"}]},
            [("default", deque([4, "DefaultValue"]), None)],
        ),
        (
            "Valid FindInMap with a default value",
            {"Fn::FindInMap": ["foo", "first", "second", {"DefaultValue": "default"}]},
            [
                ("default", deque([4, "DefaultValue"]), None),
                ("bar", deque([2]), None),
            ],
        ),
        (
            "Valid FindInMap with a bad mapping",
            {"Fn::FindInMap": ["bar", "first", "second"]},
            [
                (
                    None,
                    deque([]),
                    ValidationError(
                        (
                            "'bar' is not one of ['foo', "
                            "'transformFirstKey', 'transformSecondKey']"
                        ),
                        path=deque(["Fn::FindInMap", 0]),
                    ),
                )
            ],
        ),
        (
            "Valid FindInMap with a bad mapping and default",
            {"Fn::FindInMap": ["bar", "first", "second", {"DefaultValue": "default"}]},
            [("default", deque([4, "DefaultValue"]), None)],
        ),
        (
            "Valid FindInMap with a bad mapping and aws no value",
            {
                "Fn::FindInMap": [
                    "bar",
                    "first",
                    "second",
                    {"DefaultValue": {"Ref": "AWS::NoValue"}},
                ]
            },
            [],
        ),
        (
            "Valid FindInMap with a bad top key",
            {"Fn::FindInMap": ["foo", "second", "first"]},
            [
                (
                    None,
                    deque([]),
                    ValidationError(
                        ("'second' is not one of ['first'] for " "mapping 'foo'"),
                        path=deque(["Fn::FindInMap", 1]),
                    ),
                )
            ],
        ),
        (
            "Valid FindInMap with a bad top key and default",
            {"Fn::FindInMap": ["foo", "second", "first", {"DefaultValue": "default"}]},
            [("default", deque([4, "DefaultValue"]), None)],
        ),
        (
            "Valid FindInMap with a bad third key",
            {"Fn::FindInMap": ["foo", "first", "third"]},
            [
                (
                    None,
                    deque([]),
                    ValidationError(
                        (
                            "'third' is not one of ['second'] for "
                            "mapping 'foo' and key 'first'"
                        ),
                        path=deque(["Fn::FindInMap", 2]),
                    ),
                )
            ],
        ),
        (
            "Valid FindInMap with a bad second key and default",
            {"Fn::FindInMap": ["foo", "first", "third", {"DefaultValue": "default"}]},
            [("default", deque([4, "DefaultValue"]), None)],
        ),
        (
            "Valid FindInMap with a transform on first key",
            {"Fn::FindInMap": ["transformFirstKey", "first", "third"]},
            [],
        ),
        (
            "Valid FindInMap with a transform on second key",
            {"Fn::FindInMap": ["transformSecondKey", "first", "third"]},
            [],
        ),
        (
            "Valid Sub with a resolvable values",
            {"Fn::Sub": ["${a}-${b}", {"a": "foo", "b": "bar"}]},
            [("foo-bar", deque([]), None)],
        ),
        (
            "Valid Sub with empty parameters",
            {"Fn::Sub": ["foo", {}]},
            [("foo", deque([]), None)],
        ),
    ],
)
def test_valid_functions(name, instance, response):
    context = Context()
    context.mappings["foo"] = Map({"first": {"second": "bar"}})
    context.mappings["transformFirstKey"] = Map({"Fn::Transform": {"second": "bar"}})
    context.mappings["transformSecondKey"] = Map({"first": {"Fn::Transform": "bar"}})

    _resolve(name, instance, response, context=context)


@pytest.mark.parametrize(
    "name,instance,response",
    [
        (
            "Invalid FindInMap with no mappings",
            {"Fn::FindInMap": [{"Ref": "MyParameter"}, "B", "C"]},
            [
                (
                    None,
                    deque([]),
                    ValidationError(
                        ("{'Ref': 'MyParameter'} is not one of []"),
                        path=deque(["Fn::FindInMap", 0]),
                    ),
                )
            ],
        ),
        (
            "Invalid FindInMap with no mappings and default value",
            {"Fn::FindInMap": ["A", "B", "C", {"DefaultValue": "default"}]},
            [("default", deque([4, "DefaultValue"]), None)],
        ),
    ],
)
def test_no_mapping(name, instance, response):
    _resolve(name, instance, response)
