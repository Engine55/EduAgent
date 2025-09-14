#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os

# Add backend directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from prompt_templates import create_prompt_templates

def test_prompts():
    print("Testing prompt functions")
    print("=" * 50)

    # Create templates
    templates = create_prompt_templates()

    # Test data
    full_state = {
        "story_framework": "Test story framework content",
        "level_details": {
            "level_1": {
                "scene_data": "Test scene data"
            }
        }
    }

    # Test 1: Scene generation prompt with full state
    print("\nTest 1: Scene generation with full state")
    try:
        scene_prompt = templates.get_level_scenes_generation_prompt()
        story_framework = full_state.get("story_framework", "")

        formatted_prompt = scene_prompt.format(
            story_framework=story_framework,
            level=1
        )

        print("SUCCESS - Scene prompt generated")
        print("Prompt length:", len(formatted_prompt))

    except Exception as e:
        print("FAILED - Scene prompt:", str(e))

    # Test 2: Scene generation prompt with partial state
    print("\nTest 2: Scene generation with partial state")
    partial_state = {"story_framework": "Test content"}

    try:
        scene_prompt = templates.get_level_scenes_generation_prompt()
        story_framework = partial_state.get("story_framework", "")

        formatted_prompt = scene_prompt.format(
            story_framework=story_framework,
            level=1
        )

        print("SUCCESS - Scene prompt with partial state")
        print("Prompt length:", len(formatted_prompt))

    except Exception as e:
        print("FAILED - Scene prompt partial:", str(e))

    # Test 3: Character generation prompt with full state
    print("\nTest 3: Character generation with full state")
    try:
        char_prompt = templates.get_level_characters_generation_prompt()
        story_framework = full_state.get("story_framework", "")
        scene_data = full_state.get("level_details", {}).get("level_1", {}).get("scene_data", "")

        formatted_prompt = char_prompt.format(
            story_framework=story_framework,
            scene_data=scene_data,
            level=1
        )

        print("SUCCESS - Character prompt generated")
        print("Prompt length:", len(formatted_prompt))

    except Exception as e:
        print("FAILED - Character prompt:", str(e))

    # Test 4: Character generation prompt with missing scene data
    print("\nTest 4: Character generation with missing scene data")
    try:
        char_prompt = templates.get_level_characters_generation_prompt()
        story_framework = full_state.get("story_framework", "")
        scene_data = ""  # Missing scene data

        formatted_prompt = char_prompt.format(
            story_framework=story_framework,
            scene_data=scene_data,
            level=1
        )

        print("SUCCESS - Character prompt with missing scene data")
        print("Prompt length:", len(formatted_prompt))

    except Exception as e:
        print("FAILED - Character prompt missing data:", str(e))

    # Test 5: Empty state
    print("\nTest 5: Empty state")
    empty_state = {}

    try:
        scene_prompt = templates.get_level_scenes_generation_prompt()
        story_framework = empty_state.get("story_framework", "")

        formatted_prompt = scene_prompt.format(
            story_framework=story_framework,
            level=1
        )

        print("SUCCESS - Scene prompt with empty state")
        print("Story framework empty:", story_framework == "")

    except Exception as e:
        print("FAILED - Empty state:", str(e))

    print("\n" + "=" * 50)
    print("Test Summary:")
    print("If all tests show SUCCESS, functions handle partial data correctly")
    print("If any test shows FAILED, need to add better error handling")

if __name__ == "__main__":
    test_prompts()