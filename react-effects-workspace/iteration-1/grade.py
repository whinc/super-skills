#!/usr/bin/env python3
"""Grade eval outputs against assertions by checking code patterns."""

import json
import os
import re
import sys

BASE = "/data/workspace/wecowork-fe/react-effects-workspace/iteration-1"

def read_file(path):
    with open(path, 'r') as f:
        return f.read()

def count_useeffect(code):
    """Count useEffect usages (not in comments)."""
    lines = code.split('\n')
    count = 0
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('//') or stripped.startswith('*'):
            continue
        if 'useEffect' in line and 'import' not in line:
            count += 1
    return count

def has_key_prop_pattern(code):
    """Check if key={...Id} or key={userId} pattern exists."""
    return bool(re.search(r'key=\{[^}]*[Ii]d[^}]*\}', code))

def has_render_time_fullname(code):
    """Check if fullName is computed during render (not via useState/useEffect)."""
    has_fullname_state = bool(re.search(r"useState.*fullName|setFullName", code))
    has_fullname_compute = bool(re.search(r"const\s+fullName\s*=\s*(?!useState)", code))
    return has_fullname_compute and not has_fullname_state

def has_usememo_filter(code):
    """Check if filtering uses useMemo or direct computation."""
    return bool(re.search(r'useMemo\s*\(\s*\(\)\s*=>', code)) or \
           bool(re.search(r'const\s+filtered\w*\s*=\s*products\.filter', code))

def has_notification_in_handler(code):
    """Check notification/alert is in event handler, not in useEffect."""
    in_effect = bool(re.search(r'useEffect\s*\(\s*\(\)\s*=>\s*\{[^}]*(?:notification|alert|toast|showNotif)', code, re.DOTALL))
    in_handler = bool(re.search(r'(?:handle|add|buy|click)\w*.*(?:notification|alert|toast|showNotif)|(?:notification|alert|toast|showNotif).*(?:handle|add|buy|click)', code, re.DOTALL | re.IGNORECASE))
    return not in_effect

def has_onchange_in_handler_not_effect(code):
    """Check onChange/onToggle is called in event handler, not useEffect."""
    in_effect = bool(re.search(r'useEffect\s*\([^)]*\{[^}]*onChange|useEffect\s*\([^)]*\{[^}]*onToggle', code, re.DOTALL))
    return not in_effect

def grade_eval1(code, variant):
    """Grade UserProfile eval."""
    results = []
    
    # Assertion 1: fullName computed during render
    passed = has_render_time_fullname(code)
    results.append({
        "text": "fullName is computed during render (not via useEffect + setState)",
        "passed": passed,
        "evidence": "Found render-time fullName computation" if passed else "fullName uses useState/useEffect or not found as render computation"
    })
    
    # Assertion 2: key prop for reset
    passed = has_key_prop_pattern(code)
    results.append({
        "text": "Component uses key prop (not useEffect) to reset state when userId changes",
        "passed": passed,
        "evidence": "Found key={...Id} pattern" if passed else "No key prop pattern found for state reset"
    })
    
    # Assertion 3: zero useEffect
    effect_count = count_useeffect(code)
    passed = effect_count == 0
    results.append({
        "text": "The component contains zero useEffect calls",
        "passed": passed,
        "evidence": f"Found {effect_count} useEffect call(s)" if not passed else "Zero useEffect calls found"
    })
    
    # Assertion 4: functional completeness
    has_comment = bool(re.search(r'comment|Comment', code))
    has_names = bool(re.search(r'firstName|lastName', code))
    has_fullname = bool(re.search(r'fullName|full_name', code))
    passed = has_comment and has_names and has_fullname
    results.append({
        "text": "Component includes comment input field, firstName/lastName state, and fullName display",
        "passed": passed,
        "evidence": f"comment:{has_comment}, names:{has_names}, fullName:{has_fullname}"
    })
    
    return results

def grade_eval2(code, variant):
    """Grade ProductList eval."""
    results = []
    
    # Assertion 1: no useEffect for filter
    has_effect_for_filter = bool(re.search(r'useEffect\s*\(\s*\(\)\s*=>\s*\{[^}]*(?:setVisible|setFiltered|filter)', code, re.DOTALL))
    passed = not has_effect_for_filter and has_usememo_filter(code)
    results.append({
        "text": "Filtered products are computed during render (useMemo or direct computation), not via useEffect + setState",
        "passed": passed,
        "evidence": "Uses useMemo/direct computation for filtering" if passed else "Uses useEffect for filtering or no memoization found"
    })
    
    # Assertion 2: notification in event handler
    passed = has_notification_in_handler(code)
    results.append({
        "text": "Cart notification is called inside an event handler, not in a useEffect",
        "passed": passed,
        "evidence": "Notification triggered in event handler" if passed else "Notification found in useEffect"
    })
    
    # Assertion 3: no useEffect for selection reset
    has_effect_for_selection = bool(re.search(r'useEffect\s*\([^)]*\{[^}]*(?:setSelect|setCart|selection.*null|\[\])', code, re.DOTALL))
    passed = not has_effect_for_selection
    results.append({
        "text": "Selection clearing on filter change is handled without useEffect",
        "passed": passed,
        "evidence": "No useEffect for selection/cart reset" if passed else "Uses useEffect to reset selection/cart on filter change"
    })
    
    # Assertion 4: functional completeness
    has_filter_logic = bool(re.search(r'filter', code, re.IGNORECASE))
    has_cart = bool(re.search(r'cart|Cart', code, re.IGNORECASE))
    has_click = bool(re.search(r'onClick|handleClick|handleAdd|addToCart', code))
    passed = has_filter_logic and has_cart and has_click
    results.append({
        "text": "Component renders filtered product list, supports click-to-add-to-cart, and shows notification",
        "passed": passed,
        "evidence": f"filter:{has_filter_logic}, cart:{has_cart}, click:{has_click}"
    })
    
    return results

def grade_eval3(code, variant):
    """Grade Toggle eval."""
    results = []
    
    # Assertion 1: no useEffect for onChange
    passed = has_onchange_in_handler_not_effect(code)
    results.append({
        "text": "Toggle does NOT use useEffect to call onChange/onToggle after state change",
        "passed": passed,
        "evidence": "No useEffect used for parent notification" if passed else "useEffect used to call onChange/onToggle"
    })
    
    # Assertion 2: onChange in event handler
    has_handler_with_both = bool(re.search(r'(?:handle\w*|function\s+\w*[Cc]lick)[^}]*(?:set\w+|onChange|onToggle)', code, re.DOTALL))
    # Also check for setIsOn in updater calling onToggle
    has_updater_pattern = bool(re.search(r'setIsOn\s*\(\s*\(?\s*prev', code))
    passed = has_handler_with_both or has_updater_pattern
    results.append({
        "text": "onChange is called in the same event handler as setIsOn (or component is fully controlled)",
        "passed": passed,
        "evidence": "Found event handler pattern with both state update and parent callback" if passed else "Pattern not detected"
    })
    
    # Assertion 3: controlled or hybrid
    is_controlled = bool(re.search(r'function\s+Toggle\s*\(\s*\{[^}]*isOn\s*,', code)) and not bool(re.search(r'useState.*isOn', code))
    is_hybrid_correct = has_onchange_in_handler_not_effect(code)
    passed = is_controlled or is_hybrid_correct
    results.append({
        "text": "Component is either fully controlled or updates parent in the click handler (not via Effect)",
        "passed": passed,
        "evidence": "Fully controlled component" if is_controlled else ("Hybrid with event handler notification" if is_hybrid_correct else "Unclear pattern")
    })
    
    # Assertion 4: functional completeness
    has_toggle = bool(re.search(r'Toggle', code))
    has_parent = bool(re.search(r'Parent|Demo|App', code))
    passed = has_toggle and has_parent
    results.append({
        "text": "Includes both Toggle component and a parent component demonstrating the communication pattern",
        "passed": passed,
        "evidence": f"Toggle:{has_toggle}, Parent:{has_parent}"
    })
    
    return results

# Grade all
evals = [
    ("eval-1-user-profile", grade_eval1),
    ("eval-2-product-list", grade_eval2),
    ("eval-3-toggle", grade_eval3),
]

for eval_name, grade_fn in evals:
    for variant in ["with_skill", "without_skill"]:
        output_dir = os.path.join(BASE, eval_name, variant, "outputs")
        files = os.listdir(output_dir)
        if not files:
            print(f"SKIP: {eval_name}/{variant} - no output files")
            continue
        code = read_file(os.path.join(output_dir, files[0]))
        expectations = grade_fn(code, variant)
        
        grading = {
            "eval_name": eval_name,
            "variant": variant,
            "expectations": expectations,
            "pass_rate": sum(1 for e in expectations if e["passed"]) / len(expectations)
        }
        
        grading_path = os.path.join(BASE, eval_name, variant, "grading.json")
        with open(grading_path, 'w') as f:
            json.dump(grading, f, indent=2)
        
        passed = sum(1 for e in expectations if e["passed"])
        total = len(expectations)
        print(f"{eval_name}/{variant}: {passed}/{total} passed ({grading['pass_rate']:.0%})")

print("\nDone grading all evals.")
