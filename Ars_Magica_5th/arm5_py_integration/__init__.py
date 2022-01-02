"""Module for providing the parts in the template.html file"""
import csv
import textwrap
from pathlib import Path

import markdown
from bs4 import BeautifulSoup as soup

from .helpers import (
    CHARACTERISTICS,
    FORMS,
    TECHNIQUES,
    enumerate_helper,
    repeat_template,
    rolltemplate,
    roll,
)
from .translations import translation_attrs, translation_attrs_setup

# Note: Python automatically concatenates strings that are separated by newlines
#       This can be used to split long strings into multiple lines


# Xp helper
def xp(
    name: str, *, suffix="_exp", adv_suffix="_advancementExp", tot_suffix="_totalExp"
) -> str:
    """
    Generate the HTML for the Xp parts of arts & abilities
    """
    return (
        "["
        f"""<input type="text" class="number_3" name="attr_{name}{suffix}" value="0"/>"""
        "/"
        f"""<input type="text" class="number_3 advance" name="attr_{name}{adv_suffix}" value="0" readonly/>"""
        "/"
        f"""<input type="text" class="number_3 total" name="attr_{name}{tot_suffix}" value="0" readonly/>"""
        "]"
    )


def alert(title: str, text: str, *, level: str = "warning", ID: str = None):
    """
    Generate the HTML to display a banner that can be permanently hidden

    This is used to inform player of important changes in updates.

    Arguments:
        text: Main text of the banner
        title: Title of the banner
        type: On of "warning", "info". The aspect of the banner
        ID: optional string ID of this banner, if you need to check if it is
            open/closed somewhere. Do NOT use numbers
    """
    if not level in ("info", "warning"):
        raise ValueError("Level must be among 'info', 'warning'")
    if ID is None:
        alert_id = alert.numid
        alert.numid += 1
    else:
        alert_id = str(ID)
        alert.strid.append(alert_id)

    indent = " " * 4 * 4
    text = str(text).replace("\n", "\n" + indent)
    return textwrap.dedent(
        f"""\
        <input type="hidden" class="alert-hidder" name="attr_alert-{alert_id}" value="0"/>
        <div class="alert alert-{level}">
            <div>
                <h3> {level.title()} - {title}</h3>
                {text}
            </div>
            <label class="fakebutton">
                <input type="checkbox" name="attr_alert-{alert_id}" value="1" /> ×
            </label>
        </div>"""
    )


# python supports attributes on function
# we use that to store the internal global variable used by the function
alert.numid = 0
alert.strid = []


def disable_old_alerts(marker: str):
    indent = " " * 4 * 3
    lines = f",\n{indent}".join(
        f'"alert-{i}": 1' for i in list(range(alert.numid)) + alert.strid
    )
    return textwrap.dedent(
        f"""\
        setAttrs({{
            "{marker}": 1,
            {lines}
        }}); """
    )


# Add new parts to this dictionary
# parts can be defined in other modules and imported if the generating
# code is long
GLOBALS = {
    # makes the module available
    "markdown": markdown,
    # makes those function available in the HTML
    "xp": xp,
    "alert": alert,
    "disable_old_alerts": disable_old_alerts,
    # Makes those values available in the HTML
    "translation_attrs": translation_attrs,
    "translation_attrs_setup": translation_attrs_setup,
    "html_header": "<!-- DO NOT MODIFY !\nThis file is automatically generated from a template. Any change will be overwritten\n-->",
    "css_header": "/* DO NOT MODIFY !\nThis file is automatically generated from a tempalte. Any change will be overwritten\n*/",
}


# Personality traits
personnality_roll = roll(
    "[[@{Personality_Trait$$_Score}]] [@{Personality_Trait$$}]",
    "(?{@{circumstantial_i18n}|0}) [@{circumstances_i18n}]",
)
personnality_template = rolltemplate(
    "generic",
    Banner="^{personality} ^{roll}",
    Label="@{Personality_Trait$$}",
    Result=f"[[ %(die)s + {personnality_roll} ]]",
)

GLOBALS["personality_trait_rows"] = repeat_template(
    textwrap.dedent(
        f"""\
        <tr>
            <td><input type="text" class="heading_2" style="width:245px" name="attr_Personality_Trait$$"/></td>
            <td><input type="text" class="number_1" style="width:70px;" name="attr_Personality_Trait$$_score"/></td>
            <td><div class="flex-container">
                <button type="roll" class="button simple-roll" name="roll_personality$$_simple" value="{personnality_template.simple}"></button>
                <button type="roll" class="button stress-roll" name="roll_personality$$_stress" value="{personnality_template.stress}"></button>
            </div></td>
        </tr>"""
    ),
    range(1, 7),
    rep_key="$$",
)


# Reputations
reputation_roll = roll(
    "[[@{Reputations$$_Score}]] [@{Reputations$$}]",
    "(?{@{circumstantial_i18n}|0}) [@{circumstances_i18n}]",
)
reputation_template = rolltemplate(
    "generic",
    Banner="^{reputation} ^{roll}",
    Label="@{Reputations$$}",
    Result=f"[[ %(die)s + {reputation_roll} ]]",
)
GLOBALS["reputation_rows"] = repeat_template(
    textwrap.dedent(
        f"""\
        <tr>
            <td><input type="text" class="heading_2" name="attr_Reputations$$"/></td>
            <td><input type="text" class="heading_2a" name="attr_Reputations$$_type"/></td>
            <td><input type="text" class="number_1" style="width:50px;" name="attr_Reputations$$_score"/></td>
            <td><div class="flex-container">
                <button type="roll" class="button simple-roll" name="roll_reputation$$_simple" value="{reputation_template.simple}"></button>
                <button type="roll" class="button stress-roll" name="roll_reputation$$_stress" value="{reputation_template.stress}"></button>
            </div></td>
        </tr>"""
    ),
    range(1, 7),
    rep_key="$$",
)


# Characteristics definitions
characteristic_roll = roll(
    "(@{%%(Char)s_Score}) [@{%%(char)s_i18n}]",
    "(@{wound_total}) [@{wounds_i18n}]",
    "([[floor(@{Fatigue})]]) [@{fatigue_i18n}]",
    "(?{@{circumstantial_i18n}|0}) [@{circumstances_i18n}]",
)
characteristic_template = rolltemplate(
    "ability",
    name="@{character_name}",
    label0="^{%%(char)s}",
    result0=f"[[ %(die)s + {characteristic_roll} ]]",
    banner="@{%%(Char)s_Description}",
    label1="^{score}",
    result1="@{%%(Char)s_Score}",
    label2="^{weakness-m}",
    result2="[[ [[floor(@{Fatigue})]] [@{fatigue_i18n}] + @{wound_total} [@{wounds_i18n}] ]]",
    label3="^{circumstances-m}",
    result3="[[(?{@{circumstantial_i18n}|0})]]",
)
GLOBALS["characteristic_rows"] = repeat_template(
    textwrap.dedent(
        f"""\
        <tr>
            <th data-i18n="%(char)s" >%(Char)s</th>
            <td><input type="text" class="heading_2" name="attr_%(Char)s_Description"/></td>
            <td><input type="text" class="number_1" name="attr_%(Char)s_Score" value="0"/></td>
            <td><input type="text" class="number_1" name="attr_%(Char)s_Aging" value="0"/></td>
            <td><div class="flex-container">
                <button type="roll" class="button simple-roll" name="roll_%(Char)s_simple" value="{characteristic_template.simple}"></button>
                <button type="roll" class="button stress-roll" name="roll_%(Char)s_stress" value="{characteristic_template.stress}"></button>
            </div></td>
        </tr>"""
    ),
    CHARACTERISTICS,
    str_key="char",
)

# Characteristic options
GLOBALS["characteristic_score_options"] = repeat_template(
    """<option value="@{%(Char)s_Score}" data-i18n="%(char)s" >%(Char)s</option>""",
    CHARACTERISTICS,
    str_key="char",
)
GLOBALS["characteristic_score_ask"] = (
    "?{@{characteristic_i18n}|"
    + "| ".join(
        "@{%(char)s_i18n}, @{%(Char)s_Score} [@{%(char)s_i18n}]"
        % {"char": char, "Char": char.capitalize()}
        for char in CHARACTERISTICS
    )
    + "}"
)
GLOBALS["characteristic_name_options"] = repeat_template(
    """<option value="%(Char)s" data-i18n="%(char)s" >%(Char)s</option>""",
    CHARACTERISTICS,
    str_key="char",
)
GLOBALS["characteristic_name_ask_attr"] = (
    "?{@{characteristic_i18n}|"
    + "| ".join(
        "@{%(char)s_i18n},@{%(char)s_Score} [@{%(char)s_i18n}]" % {"char": char}
        for char in CHARACTERISTICS
    )
    + "}"
)

# Abilities
ability_roll = roll(
    "(@{Ability_Score} + @{Ability_Puissant}) [@{Ability_name}]",
    "(@{sys_at}@{character_name}@{sys_pipe}@{Ability_CharacName}_Score@{sys_rbk}) [@{sys_at}@{character_name}@{sys_pipe}@{Ability_CharacName}_i18n@{sys_rbk}]",
    "(@{wound_total}) [@{wounds_i18n}]",
    "([[floor(@{Fatigue})]]) [@{fatigue_i18n}]",
    "(?{@{circumstantial_i18n}|0}) [@{circumstances_i18n}]",
)
ability_template = rolltemplate(
    "ability",
    name="@{character_name}",
    label0="@{Ability_name}",
    result0=f"[[ %(die)s + {ability_roll} ]]",
    banner="@{Ability_Speciality}",
    label1="^{rank}",
    result1="[[ @{Ability_Score} + @{Ability_Puissant} ]]",
    label2="@{Ability_CharacName}",
    result2="[[ @{sys_at}@{character_name}@{sys_pipe}@{Ability_CharacName}_Score@{sys_rbk} ]]",
    label3="^{weakness-m}",
    result3="[[ ([[floor(@{Fatigue})]]) [@{fatigue_i18n}] + (@{wound_total}) [@{wounds_i18n}] ]]",
    label4="^{circumstances-m}",
    result4="[[ (?{@{circumstantial_i18n}|0}) ]]",
)

GLOBALS["ability_roll_simple"] = ability_template.simple
GLOBALS["ability_roll_stress"] = ability_template.stress


# Technique definitions
GLOBALS["technique_definitions"] = repeat_template(
    textwrap.dedent(
        f"""\
        <tr>
            <td><input type="text" class="number_3" name="attr_%(Tech)s_Score" value="0"/></td>
            <td data-i18n="%(tech)s" >%(Tech)s</td>
            <td>{xp("%(Tech)s")}</td>
            <td style="text-align: center"><input type="text" class="number_3 minor" name="attr_%(Tech)s_Puissant" value="0"/></td>
        </tr>"""
    ),
    TECHNIQUES,
    str_key="tech",
)

# Technique options
GLOBALS["technique_score_options"] = repeat_template(
    """<option value="(@{%(Tech)s_Score} + @{%(Tech)s_Puissant}) [@{%(tech)s_i18n}]" data-i18n="%(tech)s" >%(Tech)s</option>""",
    TECHNIQUES,
    str_key="tech",
)
GLOBALS["technique_score_options_unlabeled"] = repeat_template(
    """<option value="@{%(Tech)s_Score} + @{%(Tech)s_Puissant}" data-i18n="%(tech)s" >%(Tech)s</option>""",
    TECHNIQUES,
    str_key="tech",
)
GLOBALS["technique_name_options"] = repeat_template(
    """<option value="%(Tech)s" data-i18n="%(tech)s" >%(Tech)s</option>""",
    TECHNIQUES,
    str_key="tech",
)

GLOBALS["technique_enumerated_options"] = repeat_template(
    """<option value="%(index)s" data-i18n="%(tech)s" >%(Tech)s</option>""",
    enumerate_helper(TECHNIQUES, [str.capitalize], start=1),
    tuple_keys=("index", "tech", "Tech"),
)

# Form definitions
form_template = textwrap.dedent(
    f"""\
    <tr>
        <td><input type="text" class="number_3" name="attr_%(Form)s_Score" value="0"/></td>
        <td data-i18n="%(form)s" >%(Form)s</td>
        <td>{xp("%(Form)s")}</td>
        <td style="text-align: center"><input type="text" class="number_3 minor" name="attr_%(Form)s_Puissant" value="0"/></td>
    </tr>"""
)
GLOBALS["form_definitions_1"] = repeat_template(
    form_template, FORMS[:5], str_key="form"
)
GLOBALS["form_definitions_2"] = repeat_template(
    form_template, FORMS[5:], str_key="form"
)

# Form options
GLOBALS["form_score_options"] = repeat_template(
    """<option value="(@{%(Form)s_Score} + @{%(Form)s_Puissant}) [@{%(form)s_i18n}]" data-i18n="%(form)s" >%(Form)s</option>""",
    FORMS,
    str_key="form",
)
GLOBALS["form_score_options_unlabeled"] = repeat_template(
    """<option value="@{%(Form)s_Score} + @{%(Form)s_Puissant}" data-i18n="%(form)s" >%(Form)s</option>""",
    FORMS,
    str_key="form",
)
GLOBALS["form_name_options"] = repeat_template(
    """<option value="%(Form)s" data-i18n="%(form)s" >%(Form)s</option>""",
    FORMS,
    str_key="form",
)

GLOBALS["form_enumerated_options"] = repeat_template(
    """<option value="%(index)s" data-i18n="%(form)s" >%(Form)s</option>""",
    enumerate_helper(FORMS, [str.capitalize], start=1),
    tuple_keys=("index", "form", "Form"),
)


# Casting rolls
## Magic tab
spontaneous_roll = roll(
    "@{Spontaneous1_Technique}",
    "@{Spontaneous1_Form}",
    "([[@{Spontaneous1_Focus}]]) [@{focus_i18n}]",
    "(@{gestures})",
    "(@{words})",
    "(@{Stamina_Score}) [@{stamina_i18n}]",
    "(@{aura}) [@{aura_i18n}]",
    "([[floor(@{Fatigue})]]) [@{fatigue_i18n}]",
    "(@{wound_total}) [@{wounds_i18n}]",
    "(?{@{modifiers_i18n}|0}) [@{modifiers_i18n}]",
)
spontaneous_template = rolltemplate(
    "arcane",
    label0="^{spontaneous} ^{casting}",
    result0=f"[[ (%(die)s + {spontaneous_roll} )/2 ]]",
    label1="^{aura}",
    result1="@{aura}",
    label2="^{weakness-m}",
    result2="[[ (@{wound_total}) [@{wounds_i18n}] + [[floor(@{fatigue})]] [@{fatigue_i18n}] ]]",
    label3="^{circumstances-m}",
    result3="[[ ?{@{modifiers_i18n}|0} ]]",
    critical="critical-spontaneous",
)
# GLOBALS["spontaneous_roll_simple"] = spontaneous_template.simple
GLOBALS["spontaneous_roll_stress"] = spontaneous_template.stress


ceremonial_roll = roll(
    "@{Ceremonial_Technique}",
    "@{Ceremonial_Form}",
    "([[@{Ceremonial_Focus}]]) [@{focus_i18n}]",
    "(@{gestures})",
    "(@{words})",
    "(@{Stamina_Score}) [@{stamina_i18n}]",
    "(@{aura}) [@{aura_i18n}]",
    "([[floor(@{Fatigue})]]) [@{fatigue_i18n}]",
    "(@{wound_total}) [@{wounds_i18n}]",
    "(@{Ceremonial_Artes_Lib}) [@{artes_i18n}]",
    "(@{Ceremonial_Philos}) [@{philos_i18n}]",
    "(?{@{modifiers_i18n}|0}) [@{modifiers_i18n}]",
)
ceremonial_template = rolltemplate(
    "arcane",
    label0="^{ceremonial} ^{casting}",
    result0=f"[[ (%(die)s + {ceremonial_roll} )/2 ]]",
    label1="^{aura}",
    result1="@{aura}",
    label2="^{weakness-m}}} ",
    result2="[[ (@{wound_total}) [@{wounds_i18n}] + [[floor(@{fatigue})]] [@{fatigue_i18n}] ]]",
    label3="^{circumstances-m}",
    result3="?{@{modifiers_i18n}|0}",
    critical="critical-spontaneous",
)

# GLOBALS["ceremonial_roll_simple"] = ceremonial_template.simple
GLOBALS["ceremonial_roll_stress"] = ceremonial_template.stress


formulaic_roll = roll(
    "@{Formulaic_Technique}",
    "@{Formulaic_Form}",
    "([[@{Formulaic_Focus}]]) [@{focus_i18n}]",
    "(@{gestures})",
    "(@{words})",
    "(@{Stamina_Score}) [@{stamina_i18n}]",
    "(@{aura}) [@{aura_i18n}]",
    "([[floor(@{Fatigue})]]) [@{fatigue_i18n}] + (@{wound_total}) [@{wounds_i18n}]",
    "(?{@{modifiers_i18n}|0}) [@{modifiers_i18n}]",
)
formulaic_template = rolltemplate(
    "arcane",
    label0="^{formulaic} ^{casting}",
    result0=f"[[ %(die)s + {formulaic_roll} ]]",
    label1="^{aura}",
    result1="@{aura}",
    label2="^{weakness-m}",
    result2="[[ (@{wound_total}) [@{wounds_i18n}] + [[floor(@{fatigue})]] [@{fatigue_i18n}] ]]",
    label3="^{circumstances-m}",
    result3="?{@{modifiers_i18n}|0}",
)

GLOBALS["formulaic_roll_simple"] = formulaic_template.simple
GLOBALS["formulaic_roll_stress"] = formulaic_template.stress


ritual_roll = roll(
    "@{Ritual_Technique}",
    "@{Ritual_Form}",
    "([[@{Ritual_Focus}]]) [@{focus_i18n}]",
    "(@{Stamina_Score}) [@{stamina_i18n}]",
    "(@{aura}) [@{aura_i18n}]",
    "(@{Ritual_Artes_Lib}) [@{artes_i18n}]",
    "(@{Ritual_Philos}) [@{philos_i18n}]",
    "(@{wound_total}) [@{wounds_i18n}]",
    "([[floor(@{fatigue})]]) [@{fatigue_i18n}]",
    "(?{@{modifiers_i18n}|0}) [@{modifiers_i18n}]",
)
ritual_template = rolltemplate(
    "arcane",
    label0="^{ritual} ^{casting}",
    result0=f"[[ %(die)s + {ritual_roll} ]]",
    label1="^{aura}",
    result1="@{aura}",
    label2="^{weakness-m}",
    result2="[[ @{wound_total}[@{wounds_i18n}] + [[floor(@{fatigue})]][@{fatigue_i18n}] ]]",
    label3="^{circumstances-m}",
    result3="?{@{modifiers_i18n}|0}",
)

GLOBALS["ritual_roll_simple"] = ritual_template.simple
GLOBALS["ritual_roll_stress"] = ritual_template.stress

## Spells
# Deferred attribute access to get the spell's technique & form values
spell_tech_value = (
    "("
    "@{sys_at}@{character_name}@{sys_pipe}@{spell_tech_name}_Score@{sys_rbk} "
    "+ @{sys_at}@{character_name}@{sys_pipe}@{spell_tech_name}_Puissant@{sys_rbk}"
    ") "
    "[@{sys_at}@{character_name}@{sys_pipe}@{spell_tech_name}_i18n@{sys_rbk}]"
)
spell_form_value = (
    "("
    "@{sys_at}@{character_name}@{sys_pipe}@{spell_form_name}_Score@{sys_rbk} "
    "+ @{sys_at}@{character_name}@{sys_pipe}@{spell_form_name}_Puissant@{sys_rbk}"
    ") "
    "[@{sys_at}@{character_name}@{sys_pipe}@{spell_form_name}_i18n@{sys_rbk}]"
)
# Export the deferred attribute access for use in the HTML since the focus depends on them
GLOBALS["spell_tech_value"] = spell_tech_value
GLOBALS["spell_form_value"] = spell_form_value


spell_roll = roll(
    "(@{Stamina_Score}) [@{stamina_i18n}]",
    f"{spell_tech_value}",
    f"{spell_form_value}",
    "([[@{spell_Focus}]]) [@{focus_i18n}]",
    "(@{spell_bonus}) [@{bonus_i18n}]",
    "(@{gestures})",
    "(@{words})",
    "(@{aura}) [@{aura_i18n}]",
    "([[floor(@{Fatigue})]]) [@{fatigue_i18n}]",
    "(@{wound_total}) [@{wounds_i18n}]",
    "(?{@{modifiers_i18n}|0}) [@{modifiers_i18n}]",
)
spell_template = rolltemplate(
    "spell",
    spell="@{spell_name}",
    character="@{character_name}",
    sigil="@{sigil}",
    roll=f"[[ (%(die)s + {spell_roll}) * [[ 1 / (1 + @{{spell_Deficiency}}) ]] ]]",
    range="@{spell_range}",
    duration="@{spell_duration}",
    target="@{spell_target}",
    effect="@{spell_note}",
    mastery="@{spell_note-2}",
    Technique="@{sys_at}@{character_name}@{sys_pipe}@{spell_tech_name}_i18n@{sys_rbk}",
    Form="@{sys_at}@{character_name}@{sys_pipe}@{spell_form_name}_i18n@{sys_rbk}",
    Level="@{spell_level}",
)

GLOBALS["spell_roll_simple"] = spell_template.simple
GLOBALS["spell_roll_stress"] = spell_template.stress


# Botch formula

GLOBALS["botch_separate"] = (
    "&{template:botch} {{roll= "
    + (
        "?{@{botch_num_i18n} | "
        + "|".join(
            f"{n} {'Die' if n==1 else 'Dice'}," + " ".join(["[[1d10cf10cs0]]"] * n)
            for n in range(1, 9)
        )
        + "}"
    )
    + " }} {{type=Grouped}}"
)

# Fatigue
add_fatigue_lvl_num = 10
GLOBALS["fatigue_levels_options"] = repeat_template(
    """<option value="%%">%%</option>""", range(0, add_fatigue_lvl_num + 1)
)
GLOBALS["additional_fatigue_levels"] = repeat_template(
    textwrap.dedent(
    """\
    <tr class="addfatigue-%(num)s">
        <td><input type="radio" class="radio_1" name="attr_Fatigue" value="%(value)s"><span></span></td>
        <td style="text-align:center;">0</td>
        <td>2 min.</td>
        <td data-i18n="winded" >Winded</td>
    </tr>"""
    ),
    [(str(i), str(i / 1000)) for i in range(1, add_fatigue_lvl_num + 1)],
    tuple_keys=("num", "value"),
)
GLOBALS["fatigue_level_css"] = "\n".join(
    (
        # IF the fatigue selector is not on a value for which the level is visible
        "".join(
            ':not(.sheet-fatigue-proxy[value="%s"])' % val
            for val in range(lvl, add_fatigue_lvl_num + 1)
        )
        # THEN hide the level
        + (" + table tr.sheet-addfatigue-%s" % lvl)
        + " {\n    display: none;\n}"
    )
    for lvl in range(1, add_fatigue_lvl_num + 1)
)


# Documentation
with open(Path(__file__).parents[1] / "documentation.md") as f:
    html = markdown.markdown("".join(f))
html = soup(html, "html.parser")
for i in range(1, 10):
    for tag in html.find_all(f"h{i}"):
        tag.attrs["class"] = tag.get("class", "") + " heading_label"
GLOBALS["documentation"] = html.prettify()


# Rolltemplate
## colors for the "custom" rolltemplate
with open(Path(__file__).parent / "css_colors.csv", newline="") as f:
    reader = csv.DictReader(f)
    css_rules = []
    for color_def in reader:
        # Base CSS rules
        lines_header = [
            f".sheet-rolltemplate-custom .sheet-crt-container.sheet-crt-color-{color_def['color']} {{",
            f"    --header-bg-color: {color_def['hex']};",
        ]
        lines_rolls = [
            f".sheet-rolltemplate-custom .sheet-crt-container.sheet-crt-rlcolor-{color_def['color']} .inlinerollresult {{",
            f"    --roll-bg-color: {color_def['hex']};",
        ]
        lines_buttons = [
            f".sheet-rolltemplate-custom .sheet-crt-container.sheet-crt-btcolor-{color_def['color']} a {{",
            f"    --button-bg-color: {color_def['hex']};",
        ]

        # Adapt text color to background color
        hex = color_def["hex"].lstrip("#")
        r, g, b = tuple(int(hex[2 * i : 2 * i + 2], 16) / 255 for i in range(3))
        # Assuming sRGB -> Luma
        # may need fixing, color spaces are confusing
        luma = 0.2126 * r + 0.7152 * g + 0.0722 * b
        if luma > 0.5:  # arbitrary threshold
            # switch to black text if luma is high enough
            lines_header.append("    --header-text-color: #000;")
            lines_buttons.append("    --button-text-color: #000;")
        if luma < 0.5:
            lines_rolls.append("    --roll-text-color: #FFF;")

        # Build the rules
        for lines in (lines_header, lines_rolls, lines_buttons):
            lines.append("}")
            css_rules.append("\n".join(lines))

    GLOBALS["custom_rt_color_css"] = "\n".join(css_rules)
