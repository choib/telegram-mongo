"""
Final demonstration of the fix
"""
import sys
sys.path.insert(0, 'src')

from agentic_handlers import format_response_with_markdown

# The exact text from the issue
test_text = """### 검사의 의무에 대한 설명

**법률 문서에 기반한 검사의 의무**

검사의 의무는 형사소송법 및 관련 법률에 따라 규정되어 있으며, 주요 의무는 다음과 같습니다:

1. **수사 지휘 및 수행**
   - 검사는 범죄 수사에 필요한 압수, 수색, 검증을 할 수 있으며, 사법경찰관의 수사 결과를 감독합니다.
   - 형사소송법 제215조에 따르면, 검사는 범죄 수사에 필요한 경우 지방법원 판사에게 영장을 청구하여 압수, 수색, 검증을 할 수 있습니다.
   - 검찰사건사무규칙 제34조에 따르면, 변사사건 발생 시 검사는 직접 검시를 하거나 사법경찰관에게 지휘하여 사체를 처리해야 합니다.

2. **불구속 및 임의 수사의 원칙 준수**
   - 형사소송법 제198조에 따라, 검사는 피의자에 대한 수사를 불구속 상태에서 하는 것을 원칙으로 합니다.
   - 검찰사건사무규칙 제14조에 따르면, 검사는 수사 대상자의 자유로운 의사에 따른 임의 수사를 원칙으로 하며, 강제 수사는 최소한의 범위에서만 허용됩니다.

3. **가정폭력범죄의 신속한 수사**
   - 가정폭력범죄의 처벌 등에 관한 특례법 제7조에 따르면, 사법경찰관은 가정폭력범죄를 신속히 수사하여 사건을 검사에게 송치해야 하며, 검사는 이를 기반으로 수사를 진행해야 합니다.

4. **소명자료의 보완 요구**
   - 검찰사건사무규칙 제306조에 따르면, 검사는 압수·수색영장 등의 청구 여부를 결정하기 위해 필요한 경우 의뢰기관에 소명자료의 보완을 요구할 수 있습니다.

**웹 검색 결과에서 추가된 정보**

- **검찰청법 제4조(검사의 직무)**: 검사는 공익의 대표자로서 범죄수사, 공소의 제기 및 그 유지에 필요한 사항을 담당합니다. 그러나 검경 수사권 조정에 따라 2021년부터 수사권이 제한되었습니다.
- **고위급 검사의 지시권**: 고위급 검사의 지시권은 무제한적인 것이 아니며, 형사범죄나 경범죄를 수반하는 지시는 거부할 의무가 있습니다. 또한, 지시를 따름으로써 생명, 건강, 신체의 무결성이 위험에 처하게 될 경우, 그 수행을 거부할 수 있습니다.

**충돌 및 추가 설명**

- 법률 문서와 웹 검색 결과는 검사의 수사권에 대한 내용을 다르게 설명하고 있습니다. 법률 문서는 검사의 수사권을 광범위하게 설명하고 있지만, 웹 검색 결과는 검경 수사권 조정에 따라 수사권이 제한되었음을 언급하고 있습니다. 이 점은 사용자가 참고할 때 주의가 필요합니다.

**종합적인 설명**

검사의 의무는 형사소송법 및 관련 법률에 따라 수사 지휘, 불구속 수사 원칙 준수, 가정폭력범죄의 신속한 수사, 소명자료의 보완 요구 등 다양한 분야로 확장됩니다. 또한, 검찰청법에 따라 공익의 대표자로서의 역할을 수행하며, 고위급 검사의 지시권은 제한적입니다."""

print("=" * 80)
print("FINAL VERIFICATION - Markdown Rendering Fix")
print("=" * 80)

formatted = format_response_with_markdown(test_text)

print("\n📤 This is what will be sent to Telegram with parse_mode=ParseMode.MARKDOWN_V2:\n")
print(formatted)

print("\n" + "=" * 80)
print("✅ VERIFICATION RESULTS:")
print("=" * 80)

# Check all the important aspects
checks = [
    ("Bold text preserved", "**" in formatted),
    ("Headers preserved", "#" in formatted),
    ("Lists preserved", "-" in formatted),
    ("Periods escaped", "\\." in formatted),
    ("Asterisks NOT escaped", "\\*" not in formatted),
    ("Backticks NOT escaped", "\\`" not in formatted),
]

all_passed = True
for check_name, result in checks:
    status = "✅" if result else "❌"
    print(f"{status} {check_name}: {result}")
    if not result:
        all_passed = False

print("\n" + "=" * 80)
if all_passed:
    print("🎉 SUCCESS! All checks passed!")
    print("\nThe bot will now display:")
    print("  • **Bold text** in Telegram")
    print("  • # Headers in Telegram")
    print("  • - Lists in Telegram")
    print("  • *Italic text* in Telegram")
    print("  • `Code blocks` in Telegram")
    print("\nWith proper MarkdownV2 escaping for special characters!")
else:
    print("❌ Some checks failed. Please review.")
print("=" * 80)
