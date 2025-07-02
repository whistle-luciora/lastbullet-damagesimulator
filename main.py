import streamlit as st
import math
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import random
# matplotlib.font_manager は matplotlib-fontja を使用するため不要です。
# matplotlib.font_manager is not needed as matplotlib-fontja is used.
# import matplotlib.font_manager as fm

# matplotlib-fontja をインポートして日本語フォントを自動設定します。
# Import matplotlib-fontja to automatically set Japanese fonts.
import matplotlib_fontja

# --- バージョン情報 ---
# --- Version Information ---
__version__ = "0.1.0-beta.1"

# --- ラスバレの仕様データ ---
# --- Last Bullet Game Data ---

# メモリアスキル効果
# Memoria Skill Effects
MEMORIA_SKILL_EFFECT_RATE = {
    "AⅣ": 0.15, "AⅤ": 0.165, "AⅥ": 0.18, # AⅤ,AⅥは未検証 / AⅤ,AⅥ unverified
    "BⅢ": 0.10, "BⅣ": 0.11, "BⅤ": 0.12, # BⅤは未検証 / BⅤ unverified
    "DⅢ": 0.085, "DⅣ": 0.10
}

# 攻撃カテゴリのオプションと詳細
# Attack Category Options and Details
ATTACK_CATEGORY_OPTIONS = {
    "通常単体": {"通特": "通常", "target_range": "単体", "subtypes": ["AⅣ", "AⅤ", "AⅥ"]},
    "通常範囲": {"通特": "通常", "target_range": "範囲", "subtypes": ["BⅢ", "BⅣ", "BⅤ"]},
    "特殊単体": {"通特": "特殊", "target_range": "単体", "subtypes": ["AⅣ", "AⅤ", "AⅥ"]},
    "特殊範囲": {"通特": "特殊", "target_range": "範囲", "subtypes": ["DⅢ", "DⅣ"]}
}

# メモリアの凸と倍率
# Memoria Breakthrough and Multiplier
BREAKTHROUGH_MULTIPLIER_RATE = {
    "0凸": 1.35, "1凸": 1.375, "2凸": 1.4, "3凸": 1.425, "4凸": 1.5
}

# 補助スキルの増幅倍率
# Support Skill Amplification Rate
SUPPORTSKILL_DAMAGEUP_RATE = {
    "なし": 0.0, # None
    "ダメージUPⅠ": 0.10, "ダメージUPⅡ": 0.15, "ダメージUPⅢ": 0.18, "ダメージUPⅣ": 0.21, "ダメージUPⅤ": 0.24,
    "ダメージUPⅣ+": 0.21, # 基本倍率は同じだが、発動確率が異なる / Same base multiplier, but different activation probability
    "ダメージUPⅤ+": 0.24, # 基本倍率は同じだが、発動確率が異なる / Same base multiplier, but different activation probability
    "ダメージUPⅤ++": 0.24 # 基本倍率は同じだが、発動確率が異なる / Same base multiplier, but different activation probability
}

# 補助スキルの発動確率
# Support Skill Activation Probability
ACTIVATION_PROBABILITY = {
    "0凸": 0.12, "1凸": 0.125, "2凸": 0.13, "3凸": 0.135, "4凸": 0.15
}

# 攻撃の属性オプション
# Attack Element Options
ELEMENT_OPTIONS = ["火", "水", "風", "光", "闇"] # Fire, Water, Wind, Light, Dark

# 各種補正の定数
# Various Correction Constants
LEGION_MATCH_CORRECTION = 1.28
GRACE_PERCENTAGE = 0.10
NEUNWELT_PERCENTAGE = 1.00
STACK_METEOR_PERCENTAGE = 0.2
STACK_BARRIER_PERCENTAGE = 0.3
MIN_FINAL_DAMAGE = 2
CRITICAL_MULTIPLIER = 1.3
BUFF_LEVEL_TO_PERCENT_MULTIPLIER = 5

# 攻撃バフと防御バフの固定範囲
# Fixed Ranges for Attack and Defense Buffs
attack_buff_levels = [25, 20, 15, 10, 5, 0, -5, -10, -15, -20]
defense_buff_levels = [5, 0, -5, -10, -15, -20]

# --- 日本語フォント設定 (Matplotlib) ---
# matplotlib-fontja をインポートしているため、この関数は不要です。
# This function is not needed as matplotlib-fontja is imported.
# def set_japanese_font():
#     jp_fonts = ['IPAexGothic', 'IPA Gothic', 'Yu Gothic', 'Meiryo', 'TakaoGothic', 'Noto Sans CJK JP']
#     found_font = None
#     for font_name in jp_fonts:
#         if any(font_name.lower() in f.name.lower() for f in fm.fontManager.ttflist):
#             found_font = font_name
#             break
#     if found_font:
#         plt.rcParams['font.family'] = found_font
#         plt.rcParams['font.sans-serif'] = found_font
#         plt.rcParams['axes.unicode_minus'] = False
#     else:
#         st.warning("日本語フォントが見つかりませんでした。グラフの日本語表示が正しくない可能性があります。")
#         plt.rcParams['font.family'] = 'sans-serif'

# set_japanese_font() # この呼び出しも不要です。/ This call is also not needed.

# --- ダメージ計算関数群 ---
# --- Damage Calculation Functions ---

def calculate_final_stats(base_stat, buff_percent):
    """
    ユーザーが入力した基本ステータスとバフパーセンテージから最終攻撃力/防御力を計算する。
    buff_percent は、例えば -100%, +25% のような実際のパーセンテージ値（例: -100, 25）を想定している。
    Calculates final attack/defense from user-inputted base stats and buff percentages.
    buff_percent assumes actual percentage values (e.g., -100, 25).
    """
    return math.floor(base_stat * (1 + buff_percent / 100))

def calculate_memoria_multiplier(memoria_skill_effect, skill_lv_effect):
    """
    メモリアスキル効果とスキルLv効果を掛け合わせてメモリア倍率を計算する。
    Calculates the memoria multiplier by multiplying memoria skill effect and skill level effect.
    """
    return memoria_skill_effect * skill_lv_effect

def calculate_base_damage(final_atk, final_def, memoria_multiplier):
    """
    基礎ダメージを計算する。
    ([最終攻撃力] - 2/3[最終防御力]) × メモリア倍率（小数点以下切り捨て）。
    「最終攻撃力 - 2/3最終防御力」が負になる場合は0を最低値とする。
    Calculates base damage.
    ([Final ATK] - 2/3[Final DEF]) × Memoria Multiplier (rounded down).
    If "Final ATK - 2/3 Final DEF" is negative, the minimum value is 0.
    """
    base_val = max(0, final_atk - math.floor(2/3 * final_def))
    return math.floor(base_val * memoria_multiplier)

def calculate_auxiliary_skill_effect(
    memoria_list, # 25枚の補助スキルデータ (種類, 凸数, 属性) / 25 support skill memoria data (type, breakthrough, element)
    selected_main_memoria_attribute, # メインメモリアの属性 / Main memoria element
    legendary_amplification_per_attribute_totals, # 属性ごとのレジェンダリー合計増幅 / Total legendary amplification per element
    lily_aux_prob_amp_per_attribute_totals, # リリィの補助スキル確率増幅 (全属性の増幅値) / Lily's support skill probability amplification (amplification value for all elements)
    selected_aux_prob_amp_element # リリィの補助スキル確率増幅で選択された属性 / Selected element for Lily's support skill probability amplification
):
    """
    補助スキル効果を計算する。
    25枚のメモリアの発動をシミュレートし、合計増幅倍率を返す。
    レジェンダリースキルの増幅は属性ごとの合計値として加算される。
    リリィの補助スキル確率増幅は、対応する属性の補助スキルの発動確率に加算される。
    Calculates the support skill effect.
    Simulates the activation of 25 memoria and returns the total amplification multiplier.
    Legendary skill amplification is added as a total value per element.
    Lily's support skill probability amplification is added to the activation probability of corresponding element support skills.
    """
    total_raw_amplification_percentage = 0.0 # メインメモリアスキル効果が乗る前の生の値 / Raw value before main memoria skill effect is applied

    # 通常の補助スキル (ダメージUP) の発動判定
    # Activation judgment for normal support skills (Damage UP)
    for memoria in memoria_list:
        skill_type = memoria["種類"] # Type
        breakthrough = memoria["凸数"] # Breakthrough
        aux_memoria_attribute = memoria["属性"] # 補助メモリアの属性を取得 / Get support memoria element

        if skill_type != "なし": # If not "None"
            base_activation_probability = ACTIVATION_PROBABILITY.get(breakthrough, 0.0)
            adjusted_activation_probability = base_activation_probability

            # ダメージUPⅣ+ / V+ / V++ による発動確率調整
            # Activation probability adjustment by Damage UP IV+ / V+ / V++
            if skill_type == "ダメージUPⅣ+":
                adjusted_activation_probability *= 1.5
            elif skill_type == "ダメージUPⅤ+":
                adjusted_activation_probability *= 1.5
            elif skill_type == "ダメージUPⅤ++":
                adjusted_activation_probability *= 2.0

            # リリィの補助スキル確率増幅を加算 (補助メモリアの属性と、UIで選択された増幅対象属性が一致する場合)
            # Add Lily's support skill probability amplification (if support memoria element matches selected amplification target element in UI)
            if aux_memoria_attribute == selected_aux_prob_amp_element:
                adjusted_activation_probability += lily_aux_prob_amp_per_attribute_totals.get(selected_aux_prob_amp_element, 0.0)

            if random.random() < adjusted_activation_probability:
                # ダメージUPスキルが発動した場合、その凸数に応じた倍率を掛けて生の発動割合を加算
                # 補助スキルの効果値 (SUPPORTSKILL_DAMAGEUP_RATE) に、凸による倍率 (BREAKTHROUGH_MULTIPLIER_RATE) を乗算
                # If Damage UP skill activates, add raw activation rate by multiplying its breakthrough-dependent multiplier.
                # Multiply support skill effect value (SUPPORTSKILL_DAMAGEUP_RATE) by breakthrough multiplier (BREAKTHROUGH_MULTIPLIER_RATE).
                breakthrough_multiplier = BREAKTHROUGH_MULTIPLIER_RATE.get(breakthrough, 1.0)
                total_raw_amplification_percentage += SUPPORTSKILL_DAMAGEUP_RATE.get(skill_type, 0.0) * breakthrough_multiplier

    # レジェンダリースキルによる増幅効果を加算 (メインメモリア属性と一致する場合)
    # ユーザーが属性ごとに合計値を入力するため、それを直接加算する
    # Add amplification effect from Legendary Skills (if it matches the main memoria element).
    # Since the user inputs the total value per element, add it directly.
    total_raw_amplification_percentage += legendary_amplification_per_attribute_totals.get(selected_main_memoria_attribute, 0.0)

    # 最終的な補助スキル効果のファクター
    # Final support skill effect factor
    return 1 + total_raw_amplification_percentage


def calculate_status_ratio_correction(final_atk, final_def):
    """
    ステータス比補正を計算する。
    【最終攻撃力 / 最終防御力 ≧ 2】を満たした時に発生する補正。
    指定されたルールに基づき補正率を適用し、最終的な乗算ファクター (1 + 補正率) を返す。
    防御力が0以下の場合は最大補正を適用。
    Calculates status ratio correction.
    Correction occurs when [Final ATK / Final DEF >= 2].
    Applies correction rate based on specified rules and returns the final multiplication factor (1 + correction rate).
    If defense is 0 or less, applies maximum correction.
    """
    if final_def <= 0:
        return 1.50 # 最大補正 +50% / Max correction +50%

    ratio = final_atk / final_def
    correction_rate = 0.0

    if ratio < 2:
        correction_rate = 0.0 # 補正なし / No correction
    elif 2 <= ratio < 10:
        correction_rate = math.floor(ratio) * 0.05
    else: # ratio >= 10
        correction_rate = 0.50 # 上限50% / Upper limit 50%

    return 1 + correction_rate


def calculate_total_correction_factor(
    lily_role_correction_factor,    # リリィ役職補正 / Lily Role Correction
    lily_attribute_correction_factor, # リリィ属性補正 / Lily Element Correction
    charm_rate,                     # CHARM補正 / CHARM Correction
    order_rate,                     # オーダー効果 (単一値) / Order Effect (single value)
    auxiliary_skill_factor,         # 補助スキル効果 / Support Skill Effect
    grace_active,                   # 恩恵 / Grace
    neunwelt_active,                # ノインヴェルト / Neunwelt
    status_ratio_correction_factor, # ステータス比補正 / Status Ratio Correction
    legion_match_active,            # レギマ補正 (常時True) / Legion Match Correction (always True)
    stack_meteor_active,            # スタック補正 (メテオ) / Stack Correction (Meteor)
    stack_barrier_active,           # スタック補正 (バリア) / Stack Correction (Barrier)
    counter_correction_rate,        # カウンター補正 / Counter Correction
    theme_correction_rate,          # テーマ補正 / Theme Correction
    opponent_costume_attribute,     # 相手の衣装属性 / Opponent Costume Element
    opponent_costume_reduction_rate,# 相手の衣装ダメージ軽減率 / Opponent Costume Damage Reduction Rate
    selected_attribute              # メインメモリアの属性 / Main Memoria Element
):
    """
    各種補正の合計乗算ファクターを計算する。
    断り書きがない限り全てかけ合わせ。恩恵+ノインヴェルトは足し合わせる。スタック補正は乗算。
    レギマ補正は常にTrueとして計算。
    Calculates the total multiplication factor for various corrections.
    All are multiplied unless otherwise specified. Grace + Neunwelt are added. Stack correction is multiplied.
    Legion Match Correction is always calculated as True.
    """

    # 基本の乗算補正 (全てかけ合わせ)
    # Basic Multiplication Correction (all multiplied)
    factor = 1.0
    factor *= lily_role_correction_factor # リリィ役職補正を加算 / Add Lily role correction
    factor *= lily_attribute_correction_factor # リリィ属性補正を加算 / Add Lily element correction

    factor *= charm_rate
    factor *= order_rate # 単一のオーダー効果倍率を適用 / Apply single order effect multiplier
    factor *= auxiliary_skill_factor # 補助スキル効果 / Support skill effect
    factor *= status_ratio_correction_factor
    factor *= counter_correction_rate
    factor *= theme_correction_rate

    # レギマ補正は常にTrue
    # Legion Match Correction is always True
    if legion_match_active: # このパラメータは常にTrueで渡される想定 / This parameter is expected to be always True
        factor *= LEGION_MATCH_CORRECTION

    # スタック補正 (加算・減算してから乗算)
    # メテオとバリアが同時に発動した場合の計算は (1 + 0.2 - 0.3) となる
    # Stack Correction (add/subtract then multiply)
    # If Meteor and Barrier activate simultaneously, the calculation is (1 + 0.2 - 0.3)
    stack_correction_factor = 1.0
    if stack_meteor_active:
        stack_correction_factor += STACK_METEOR_PERCENTAGE # メテオ発動で+20% / Meteor activation +20%
    if stack_barrier_active:
        stack_correction_factor -= STACK_BARRIER_PERCENTAGE # バリア発動で-30% / Barrier activation -30%
    factor *= stack_correction_factor

    # 相手の衣装補正
    # Opponent Costume Correction
    if opponent_costume_attribute != "なし" and opponent_costume_attribute == selected_attribute:
        factor *= (1 - opponent_costume_reduction_rate)

    # 恩恵とノインヴェルトの補正
    # Grace and Neunwelt Correction
    grace_neunwelt_correction_total = 0.0 # 変数名を変更 / Variable name changed
    if grace_active:
        grace_neunwelt_correction_total += GRACE_PERCENTAGE # +10%
    if neunwelt_active:
        grace_neunwelt_correction_total += NEUNWELT_PERCENTAGE # +100%
    factor *= (1 + grace_neunwelt_correction_total)

    return factor


def simulate_damage(
    base_atk, base_spattack, base_def, base_spdefence,
    attack_buff_percent, defense_buff_percent,
    attribute_atk_buff_value, attribute_def_buff_value, # 属性バフの値を追加 / Add attribute buff values
    selected_attack_subtype, selected_breakthrough_multiplier_rate, selected_attribute,
    selected_attack_category_label, # "通常単体"などのカテゴリラベル (役職補正用) / Category label like "Normal Single" (for role correction)
    memoria_aux_data_list, # 25枚の補助スキルデータ (種類, 凸数, 属性) / 25 support skill memoria data (type, breakthrough, element)
    legendary_amplification_per_attribute_totals, # 新しいレジェンダリー合計増幅データ / New legendary total amplification data
    lily_role_selection_label, lily_role_correction_rate, # リリィ役職設定 / Lily Role Settings
    lily_aux_prob_amp_per_attribute_totals, selected_aux_prob_amp_element, # リリィ補助スキル確率増幅 (全属性の値) / Lily Support Skill Probability Amplification (value for all elements)
    lily_attribute_selection, lily_attribute_correction_multiplier, # リリィ属性補正 / Lily Element Correction
    charm_rates, order_rate, counter_rate, theme_rates, # order_rate は単一値 / order_rate is a single value
    grace_active, neunwelt_active, # legion_match_active は常にTrue / legion_match_active is always True
    stack_meteor_active, stack_barrier_active,
    critical_active,
    opponent_costume_attribute, # 相手の衣装属性を直接渡す / Pass opponent costume element directly
    opponent_costume_reduction_rate # 相手の衣装ダメージ軽減率を直接渡す / Pass opponent costume damage reduction rate directly
):
    """
    ラスバレのダメージ計算を一回分シミュレーションする。
    全計算ステップを統合し、最終ダメージを返す。
    Simulates a single Last Bullet damage calculation.
    Integrates all calculation steps and returns the final damage.
    """

    # 攻撃タイプに応じて使用するATKとDEFを選択
    # Select ATK and DEF to use based on attack type
    attack_type = ATTACK_CATEGORY_OPTIONS[selected_attack_category_label]["通特"]

    current_base_atk = 0
    current_base_def = 0

    if attack_type == "通常": # Normal
        current_base_atk = base_atk
        current_base_def = base_def
    elif attack_type == "特殊": # Special
        current_base_atk = base_spattack
        current_base_def = base_spdefence

    # 1. 最終攻撃力, 最終防御力の計算 (通常バフ適用後)
    # 1. Calculate Final ATK, Final DEF (after normal buff application)
    final_atk = calculate_final_stats(current_base_atk, attack_buff_percent)
    final_def = calculate_final_stats(current_base_def, defense_buff_percent)

    # 属性バフの値を加算
    # Add attribute buff values
    final_atk += attribute_atk_buff_value
    final_def += attribute_def_buff_value

    # 2. メモリア倍率の計算
    # 2. Calculate Memoria Multiplier
    memoria_skill_effect = MEMORIA_SKILL_EFFECT_RATE.get(selected_attack_subtype, 0.1) # 未設定の場合のデフォルト値 / Default value if not set
    skill_lv_effect = BREAKTHROUGH_MULTIPLIER_RATE.get(selected_breakthrough_multiplier_rate, 1.35) # 未設定の場合のデフォルト値 / Default value if not set
    memoria_multiplier = calculate_memoria_multiplier(memoria_skill_effect, skill_lv_effect)

    # 3. 基礎ダメージの計算
    # 3. Calculate Base Damage
    base_damage = calculate_base_damage(final_atk, final_def, memoria_multiplier)

    # 4. 各種補正の計算
    # 4. Calculate Various Corrections
    # リリィ役職補正の計算
    # Calculate Lily Role Correction
    lily_role_correction_factor = 1.0
    lily_target_range = ATTACK_CATEGORY_OPTIONS[lily_role_selection_label]["target_range"]
    main_memoria_target_range = ATTACK_CATEGORY_OPTIONS[selected_attack_category_label]["target_range"]
    if lily_target_range == main_memoria_target_range:
        lily_role_correction_factor = lily_role_correction_rate

    # リリィ属性補正の計算
    # Calculate Lily Element Correction
    lily_attribute_correction_factor = 1.0
    if lily_attribute_selection != "なし" and lily_attribute_selection == selected_attribute:
        lily_attribute_correction_factor = lily_attribute_correction_multiplier

    # CHARM補正、テーマ補正は、選択された属性に応じた値を辞書から取得
    # CHARM Correction, Theme Correction: Get values from dictionary based on selected element
    charm_current_rate = charm_rates.get(selected_attribute, 1.0)
    # order_rate は単一値として渡されるため、直接使用
    # order_rate is passed as a single value, so use it directly
    theme_current_rate = theme_rates.get(selected_attribute, 1.0)

    # 補助スキル効果 (シミュレーションごとに25枚のメモリアの発動判定を行い再計算)
    # Support Skill Effect (recalculate activation judgment for 25 memoria per simulation)
    auxiliary_skill_factor = calculate_auxiliary_skill_effect(
        memoria_aux_data_list, selected_attribute,
        legendary_amplification_per_attribute_totals, lily_aux_prob_amp_per_attribute_totals, selected_aux_prob_amp_element
    )

    # ステータス比補正
    # Status Ratio Correction
    status_ratio_correction_factor = calculate_status_ratio_correction(final_atk, final_def)

    # 全ての各種補正を合算した乗算ファクター
    # Total Multiplication Factor for all Corrections
    total_correction_factor = calculate_total_correction_factor(
        lily_role_correction_factor=lily_role_correction_factor,
        lily_attribute_correction_factor=lily_attribute_correction_factor,
        charm_rate=charm_current_rate,
        order_rate=order_rate,
        auxiliary_skill_factor=auxiliary_skill_factor,
        grace_active=grace_active,
        neunwelt_active=neunwelt_active,
        status_ratio_correction_factor=status_ratio_correction_factor,
        legion_match_active=True, # レギマ補正は常にTrue / Legion Match Correction is always True
        stack_meteor_active=stack_meteor_active,
        stack_barrier_active=stack_barrier_active,
        counter_correction_rate=counter_rate,
        theme_correction_rate=theme_current_rate,
        opponent_costume_attribute=opponent_costume_attribute,
        opponent_costume_reduction_rate=opponent_costume_reduction_rate,
        selected_attribute=selected_attribute
    )

    # 補正後ダメージを計算
    # Calculate Corrected Damage
    corrected_damage = math.floor(base_damage * total_correction_factor)


    # 5. 乱数処理後ダメージ
    # 5. Randomized Damage
    random_factor = random.uniform(0.9, 1.0)
    randomized_damage = math.floor(corrected_damage * random_factor)

    # 6. クリティカル補正
    # 6. Critical Correction
    critical_correction = CRITICAL_MULTIPLIER if critical_active else 1.0

    # 7. 最終ダメージ
    # 乱数処理後ダメージが負になることを避けるためにmax(0, ...)を追加し、最終ダメージが2より小さくならないようにする
    # 7. Final Damage
    # Add max(0, ...) to avoid negative randomized damage, and ensure final damage is not less than 2.
    final_damage = math.floor(MIN_FINAL_DAMAGE + (max(0, randomized_damage) * critical_correction))

    return final_damage

# ヘルパー関数: 指定されたパラメータで複数回シミュレーションを実行
# Helper function: Run multiple simulations with specified parameters
def run_multiple_simulations_for_params(
    num_sims, base_atk, base_spattack, base_def, base_spdefence,
    actual_atk_buff_percent, actual_def_buff_percent,
    attribute_atk_buff_value, attribute_def_buff_value, # 属性バフの値を追加 / Add attribute buff values
    selected_attack_subtype, selected_breakthrough_multiplier_rate, selected_attribute,
    selected_attack_category_label, memoria_aux_data_list,
    legendary_amplification_per_attribute_totals,
    lily_role_selection_label, lily_role_correction_rate, # リリィ役職設定 / Lily Role Settings
    lily_aux_prob_amp_per_attribute_totals, selected_aux_prob_amp_element, # リリィ補助スキル確率増幅 (全属性の値) / Lily Support Skill Probability Amplification (value for all elements)
    lily_attribute_selection, lily_attribute_correction_multiplier, # リリィ属性補正 / Lily Element Correction
    charm_rates, order_rate, counter_rate, theme_rates, # order_rate は単一値 / order_rate is a single value
    grace_active, neunwelt_active,
    stack_meteor_active, stack_barrier_active,
    critical_active, opponent_costume_attribute, opponent_costume_reduction_rate
):
    damages = []
    for _ in range(num_sims):
        damage = simulate_damage(
            base_atk, base_spattack, base_def, base_spdefence,
            actual_atk_buff_percent, actual_def_buff_percent,
            attribute_atk_buff_value, attribute_def_buff_value, # 属性バフの値を渡す / Pass attribute buff values
            selected_attack_subtype, selected_breakthrough_multiplier_rate, selected_attribute,
            selected_attack_category_label,
            memoria_aux_data_list, # 補助スキルデータ / Support skill data
            st.session_state.legendary_per_attribute_totals, # レジェンダリー合計増幅データ / Legendary total amplification data
            st.session_state.lily_role_selection, st.session_state.lily_role_correction_rate, # リリィ役職設定を渡す / Pass Lily role settings
            st.session_state.lily_aux_prob_amp_per_attribute_totals, # リリィ補助スキル確率増幅を渡す / Pass Lily support skill probability amplification
            st.session_state.selected_aux_prob_amp_element, # リリィ補助スキル確率増幅で選択された属性を渡す / Pass selected element for Lily support skill probability amplification
            st.session_state.lily_attribute_selection, st.session_state.lily_attribute_correction_multiplier, # リリィ属性補正を渡す / Pass Lily element correction
            charm_rates, st.session_state.global_order_rate, counter_rate, st.session_state.theme_rates, # order_rate は単一値 / order_rate is a single value
            st.session_state.grace_active, neunwelt_active, # legion_match_active は True で固定 / legion_match_active is fixed to True
            stack_meteor_active, stack_barrier_active,
            critical_active,
            opponent_costume_attribute, # 相手の衣装属性を渡す / Pass opponent costume element
            opponent_costume_reduction_rate # 相手の衣装ダメージ軽減率を渡す / Pass opponent costume damage reduction rate
        )
        damages.append(damage)
    return damages


# --- Streamlit アプリケーションの構築 ---
# --- Streamlit Application Construction ---

# ページの初期設定 (レイアウトをワイドに設定)
# Initial page settings (set layout to wide)
st.set_page_config(layout="wide")
st.markdown("<h1 style='font-size: 2.5em;'>ラスバレ ダメージシミュレーター</h1>", unsafe_allow_html=True)
st.caption(f"v{__version__}")

# --- シミュレーション設定の初期値 ---
# --- Initial Simulation Settings ---
# session_state を使用して、ページ再ロード時にもデータが保持されるようにする
# Use session_state to retain data even when the page reloads
if 'memoria_data' not in st.session_state:
    st.session_state.memoria_data = pd.DataFrame([
        {'No.': i + 1, '種類': 'なし', '凸数': '4凸', '属性': ELEMENT_OPTIONS[0]} # 属性カラムを追加, 初期値を'4凸'に設定 / Add element column, set initial value to '4凸'
        for i in range(25)
    ])

# レジェンダリースキルの各属性における増幅倍率の辞書を初期化
# Initialize dictionary for amplification rates of legendary skills for each element
if 'legendary_per_attribute_totals' not in st.session_state:
    st.session_state.legendary_per_attribute_totals = {element: 0.0 for element in ELEMENT_OPTIONS}

# Initialize session state for Lily auxiliary probability amplification
if 'lily_aux_prob_amp_per_attribute_totals' not in st.session_state:
    st.session_state.lily_aux_prob_amp_per_attribute_totals = {element: 0.0 for element in ELEMENT_OPTIONS}

# Initialize session state for Lily role if not present
if 'lily_role_selection' not in st.session_state:
    st.session_state.lily_role_selection = list(ATTACK_CATEGORY_OPTIONS.keys())[0] # Default to first role

if 'lily_role_correction_rate' not in st.session_state:
    st.session_state.lily_role_correction_rate = 1.15

# Initialize session state for Lily attribute correction
if 'lily_attribute_selection' not in st.session_state:
    st.session_state.lily_attribute_selection = "なし" # None
if 'lily_attribute_correction_multiplier' not in st.session_state:
    st.session_state.lily_attribute_correction_multiplier = 1.00


# Initialize session state for opponent costume correction
if 'opponent_costume_attribute' not in st.session_state:
    st.session_state.opponent_costume_attribute = "なし" # Default to no specific attribute
if 'opponent_costume_reduction_rate' not in st.session_state:
    st.session_state.opponent_costume_reduction_rate = 0.0

# Initialize session state for global order rate
if 'global_order_rate' not in st.session_state:
    st.session_state.global_order_rate = 1.0

# Initialize session state for selected_aux_prob_amp_element
if 'selected_aux_prob_amp_element' not in st.session_state:
    st.session_state.selected_aux_prob_amp_element = ELEMENT_OPTIONS[0] # Default to first element

# Initialize session state for grace_active
if 'grace_active' not in st.session_state:
    st.session_state.grace_active = True # Default to True

# Initialize session state for CHARM_rates
if 'charm_rates' not in st.session_state:
    st.session_state.charm_rates = {element: 1.1 for element in ELEMENT_OPTIONS} # Default to 1.1

# Initialize session state for theme_rates
if 'theme_rates' not in st.session_state:
    st.session_state.theme_rates = {
        "火": 1.1, "水": 1.1, "風": 1.1, # Fire, Water, Wind
        "光": 1.0, "闇": 1.0 # Light, Dark
    }


# --- シミュレーション条件入力欄 (サイドバー) ---
# --- Simulation Condition Input (Sidebar) ---
with st.sidebar:
    st.header("シミュレーション条件設定") # Simulation Condition Settings

    # 1. キャラステータス
    # 1. Character Stats
    st.subheader("キャラステータス") # Character Stats
    with st.expander("詳細設定", expanded=True): # Detailed Settings
        base_attack = st.number_input("攻撃側 ATK", value=500000, min_value=1, step=10000, key="attack") # Attacker ATK
        base_spattack = st.number_input("攻撃側 Sp.ATK", value=500000, min_value=1, step=10000, key="spattack") # Attacker Sp.ATK
        base_defence = st.number_input("防御側 DEF", value=300000, min_value=1, step=10000, key="defence") # Defender DEF
        base_spdefence = st.number_input("防御側 Sp.DEF", value=300000, min_value=1, step=10000, key="spdefence") # Defender Sp.DEF
        target_hp = st.number_input("防御側 HP", value=1500000, min_value=1, step=10000, key="hp") # Defender HP

    # 2. 攻撃側の使用スキル設定
    # 2. Attacker's Skill Settings
    st.subheader("使用スキル設定") # Skill Settings
    with st.expander("レギマスキル", expanded=True): # Legion Match Skill
        selected_attack_category_label = st.radio(
            "メモリア種別", # Memoria Type
            list(ATTACK_CATEGORY_OPTIONS.keys()),
            key="selected_attack_category_radio",
            index=0
        )

        selected_category_dict = ATTACK_CATEGORY_OPTIONS[selected_attack_category_label]
        selected_attack_subtype = st.selectbox(
            "メモリア詳細種別", # Memoria Subtype
            selected_category_dict["subtypes"],
            key="selected_attack_subtype_select",
            help="BⅤ,DⅢ,DⅣは検証データがないため、仮の値での実装です。", # BⅤ,DⅢ,DⅣ are implemented with provisional values as there is no verification data.
            index=0
        )

        selected_breakthrough_multiplier_rate = st.selectbox(
            "凸数", # Breakthrough Count
            list(BREAKTHROUGH_MULTIPLIER_RATE.keys()),
            key="selected_breakthrough_multiplier_rate",
            index=list(BREAKTHROUGH_MULTIPLIER_RATE.keys()).index("4凸") # 初期値を"4凸"に設定 / Set initial value to "4凸"
        )

        selected_attribute = st.radio(
            "属性", # Element
            ELEMENT_OPTIONS,
            key="selected_attribute",
            horizontal=True,
        )

        counter_rate = st.number_input(
            "カウンター補正倍率", # Counter Correction Multiplier
            min_value=0.0, value=1.0, step=0.1, format="%.1f",
            key="counterattack_rate",
        )

    # 3. 補助スキル設定
    # 3. Support Skill Settings
    with st.expander("補助スキル", expanded=True): # Support Skill

        # `st.data_editor` を使用して、25枚のメモリアの詳細を設定
        # Use `st.data_editor` to set details for 25 memoria
        edited_memoria_data = st.data_editor(
            st.session_state.memoria_data,
            column_config={
                "No.": st.column_config.NumberColumn("No.", help="メモリアの番号", disabled=True), # Memoria Number
                "種類": st.column_config.SelectboxColumn(
                    "種類", # Type
                    options=list(SUPPORTSKILL_DAMAGEUP_RATE.keys()),
                    required=True,
                ),
                "凸数": st.column_config.SelectboxColumn(
                    "凸数", # Breakthrough Count
                    options=list(BREAKTHROUGH_MULTIPLIER_RATE.keys()),
                    required=True,
                ),
                "属性": st.column_config.SelectboxColumn( # 新しい属性カラムを追加 / Add new element column
                    "属性", # Element
                    options=ELEMENT_OPTIONS,
                    required=True,
                )
            },
            num_rows="fixed",
            hide_index=True,
            key="memoria_data_editor"
        )
        # 編集されたデータをセッションステートに保存
        # Save edited data to session state
        st.session_state.memoria_data = edited_memoria_data

    # 4. レジェンダリーメモリア設定
    # 4. Legendary Memoria Settings
    with st.expander("レジェンダリーメモリア", expanded=True): # Legendary Memoria
        legendary_amplification_per_attribute_totals = {}
        for element in ELEMENT_OPTIONS:
            legendary_amplification_per_attribute_totals[element] = st.number_input(
                f"{element}属性 レジェンダリー合計増幅", # {element} Element Legendary Total Amplification
                min_value=0.0, value=st.session_state.legendary_per_attribute_totals.get(element, 0.0), step=0.01, format="%.2f",
                key=f"legendary_total_amp_{element}",
                help=f"全ての{element}属性のレジェンダリーメモリアによる合計増幅倍率を入力してください。例えば、{element}属性レジェンダリースキルの増幅値が10%であれば0.10と入力します。" # Please enter the total amplification rate by all {element} element legendary memoria. For example, if the amplification value of an {element} element legendary skill is 10%, enter 0.10.
            )
        st.session_state.legendary_per_attribute_totals = legendary_amplification_per_attribute_totals

    # 5. リリィ衣装設定
    # 5. Lily Costume Settings
    st.subheader("リリィ衣装設定") # Lily Costume Settings
    with st.expander("詳細設定", expanded=True): # Detailed Settings
        st.markdown("<b>リリィ衣装補正</b>", unsafe_allow_html=True) # Lily Costume Correction
        st.session_state.lily_role_selection = st.selectbox(
            "リリィの役職", # Lily's Role
            options=list(ATTACK_CATEGORY_OPTIONS.keys()),
            key="lily_role_select",
            index=list(ATTACK_CATEGORY_OPTIONS.keys()).index(st.session_state.lily_role_selection),
        )
        st.session_state.lily_role_correction_rate = st.number_input(
            "役職一致補正倍率", # Role Match Correction Multiplier
            min_value=1.0, value=st.session_state.lily_role_correction_rate, step=0.01, format="%.2f",
            key="lily_role_correction_input",
        )


        st.markdown("---") # Separator

        # リリィ属性補正 (リリィ衣装設定の中に移動)
        # Lily Element Correction (moved inside Lily Costume Settings)
        st.markdown("<b>リリィ属性補正</b>", unsafe_allow_html=True) # Lily Element Correction
        st.session_state.lily_attribute_selection = st.selectbox(
            "リリィの属性", # Lily's Element
            options=ELEMENT_OPTIONS + ["なし"], # None
            key="lily_attribute_select",
            index=ELEMENT_OPTIONS.index(st.session_state.get('lily_attribute_selection', ELEMENT_OPTIONS[0])) if st.session_state.get('lily_attribute_selection', ELEMENT_OPTIONS[0]) in ELEMENT_OPTIONS else len(ELEMENT_OPTIONS),
        )
        st.session_state.lily_attribute_correction_multiplier = st.number_input(
            "属性一致補正倍率", # Element Match Correction Multiplier
            min_value=1.00, value=st.session_state.get('lily_attribute_correction_multiplier', 1.05), step=0.01, format="%.2f", # 初期値を1.05に変更 / Change initial value to 1.05
            key="lily_attribute_correction_input",
        )


        st.markdown("---") # Separator

        st.markdown("<b>補助スキル確率増幅</b>", unsafe_allow_html=True) # Support Skill Probability Amplification

        # 補助スキル確率増幅対象の属性を選択
        # Select target element for support skill probability amplification
        st.session_state.selected_aux_prob_amp_element = st.selectbox(
            "確率増幅対象属性", # Target Element for Probability Amplification
            options=ELEMENT_OPTIONS,
            key="selected_aux_prob_amp_element_sidebar",
            index=ELEMENT_OPTIONS.index(st.session_state.selected_aux_prob_amp_element),
        )

        # 選択された属性に対する増幅値を入力
        # Enter amplification value for the selected element
        current_aux_prob_amp_value = st.session_state.lily_aux_prob_amp_per_attribute_totals.get(st.session_state.selected_aux_prob_amp_element, 0.0)
        new_aux_prob_amp_value = st.number_input(
            f"{st.session_state.selected_aux_prob_amp_element}属性 確率増幅", # {element} Element Probability Amplification
            min_value=0.0, value=current_aux_prob_amp_value, step=0.01, format="%.2f",
            key=f"lily_aux_prob_amp_value_{st.session_state.selected_aux_prob_amp_element}",
        )
        # セッションステートを更新
        # Update session state
        if new_aux_prob_amp_value != current_aux_prob_amp_value:
            st.session_state.lily_aux_prob_amp_per_attribute_totals[st.session_state.selected_aux_prob_amp_element] = new_aux_prob_amp_value


    # 6. 各種補正設定
    # 6. Various Correction Settings
    st.subheader("各種補正設定") # Various Correction Settings

    # オーダー効果
    # Order Effect
    st.session_state.global_order_rate = st.number_input(
        f"オーダー効果 (全体)", # Order Effect (Overall)
        min_value=0.0, value=st.session_state.global_order_rate, step=0.05, format="%.2f",
        key=f"order_rate_global",
        help="弱点属性ダメージ増オーダーで味方と相手の両方が属性への補正をもつオーダーを使用している場合は数値を加算する。" # If using an order that increases weak element damage and both allies and enemies have element corrections, add the value.
    )

    # 恩恵
    # Grace
    grace_active = st.checkbox("恩恵 (+10%)", key="grace_active") # Grace (+10%)

    # ノインヴェルト
    # Neunwelt
    neunwelt_active = st.checkbox("ノインヴェルト (+100%)", key="neunwelt_active") # Neunwelt (+100%)

    # メテオ
    # Meteor
    stack_meteor_active = st.checkbox("メテオ (+20%)", key="stack_meteor_active") # Meteor (+20%)

    # バリア
    # Barrier
    stack_barrier_active = st.checkbox("バリア (-30%)", key="stack_barrier_active") # Barrier (-30%)

    # CHARM補正
    # CHARM Correction
    with st.expander("CHARM補正", expanded=True): # CHARM Correction
        charm_rates = {}
        for element in ELEMENT_OPTIONS:
            charm_rates[element] = st.number_input(
                f"CHARM補正 ({element})", # CHARM Correction ({element})
                min_value=0.0, value=st.session_state.charm_rates.get(element, 1.1), # Default to 1.1
                step=0.05, format="%.2f",
                key=f"charm_rate_{element}"
            )
        st.session_state.charm_rates = charm_rates # Update session state

    # 相手の衣装補正
    # Opponent Costume Correction
    with st.expander("相手の衣装補正", expanded=True): # Opponent Costume Correction
        selected_opponent_costume_attribute = st.selectbox(
            "相手の衣装属性", # Opponent Costume Element
            options=ELEMENT_OPTIONS + ["なし"], # None
            key="opponent_costume_attribute_select_sidebar", # keyが重複しないように修正 / Modified to avoid key duplication
            index=ELEMENT_OPTIONS.index(st.session_state.get('opponent_costume_attribute', ELEMENT_OPTIONS[0])) if st.session_state.get('opponent_costume_attribute', ELEMENT_OPTIONS[0]) in ELEMENT_OPTIONS else len(ELEMENT_OPTIONS),
            help="相手のリリィ衣装の属性を選択してください。攻撃スキルの属性と一致するとダメージが軽減されます。" # Select the element of the opponent's Lily costume. Damage is reduced if it matches the attack skill's element.
        )
        opponent_costume_reduction_rate = st.number_input(
            "ダメージ軽減率", # Damage Reduction Rate
            min_value=0.0, max_value=1.0, value=st.session_state.get('opponent_costume_reduction_rate', 0.05), step=0.01, format="%.2f", # 初期値を0.05に変更 / Change initial value to 0.05
            key="opponent_costume_reduction_input_sidebar", # keyが重複しないように修正 / Modified to avoid key duplication
            help="例: 0.05で5%軽減" # Example: 0.05 for 5% reduction
        )
    # Store in session state for persistence
    st.session_state.opponent_costume_attribute = selected_opponent_costume_attribute
    st.session_state.opponent_costume_reduction_rate = opponent_costume_reduction_rate

    # テーマ補正
    # Theme Correction
    with st.expander("テーマ補正", expanded=False): # expanded=False に変更 / Changed to expanded=False
        theme_rates = {}
        for element in ELEMENT_OPTIONS:
            default_theme_value = 1.1 if element in ["火", "水", "風"] else 1.0 # Fire, Water, Wind
            theme_rates[element] = st.number_input(
                f"テーマ補正 ({element})", # Theme Correction ({element})
                min_value=0.0, value=st.session_state.theme_rates.get(element, default_theme_value),
                step=0.05, format="%.2f",
                key=f"theme_rate_{element}_sidebar" # keyが重複しないように修正 / Modified to avoid key duplication
            )
        st.session_state.theme_rates = theme_rates # Update session state


    # 8. クリティカル設定
    # 8. Critical Settings
    st.subheader("クリティカル設定") # Critical Settings
    critical_active = st.checkbox("クリティカル発生 (x1.3)", key="critical_active", help="常にクリティカルが発生するものと仮定します。") # Critical Hit (x1.3) / Assume critical hit always occurs.

    # 9. シミュレーション実行設定
    # 9. Simulation Execution Settings
    st.subheader("シミュレーション実行設定") # Simulation Execution Settings
    num_simulations = st.number_input(
        "シミュレーション回数 (N)", # Number of Simulations (N)
        min_value=100, value=1000, step=100,
        key="num_simulations",
        help="最低でも1000回以上にすることを推奨します。" # It is recommended to set it to at least 1000 times or more.
    )


# --- シミュレーション実行ボタン (メインエリア) ---
# --- Simulation Execution Button (Main Area) ---
st.warning("一部のメモリアスキル効果値は未検証であり、仮の値を入れただけになっています。 \n" +
           "詳細は'ダメージ計算式'のスプレッドシートを参照してください。"
          ) # Some memoria skill effect values are unverified and are only provisional. \n Please refer to the 'Damage Calculation Formula' spreadsheet for details.

st.subheader("簡易ダメージ計算") # Simple Damage Calculation
st.write("様々な攻撃バフと防御バフでのダメージを調べたい場合はこちら") # If you want to check damage with various attack and defense buffs, click here.

if st.button("シミュレーション実行"): # Execute Simulation

    with st.spinner("シミュレーションを実行中..."): # Running simulation...
        memoria_aux_data_list = st.session_state.memoria_data.to_dict('records')

        results_data = [] # 結果を格納するリスト / List to store results

        # 各攻撃バフと防御バフの組み合わせについてシミュレーションを実行
        # Run simulations for each combination of attack and defense buffs
        for atk_level in attack_buff_levels:
            # バフレベルを実際のパーセンテージに変換 (例: -20 -> -100%)
            # Convert buff level to actual percentage (e.g., -20 -> -100%)
            actual_atk_buff_percent = atk_level * BUFF_LEVEL_TO_PERCENT_MULTIPLIER
            # 一番左上のセルに表示するテキストを直接指定
            # Directly specify the text to display in the top-left cell
            row_data = {"平均ダメ (HP割合)":f"攻撃バフ {atk_level}"} # Avg Damage (HP %): Attack Buff {atk_level}

            for def_level in defense_buff_levels:
                # バフレベルを実際のパーセンテージに変換 (例: +5 -> +25%)
                # Convert buff level to actual percentage (e.g., +5 -> +25%)
                actual_def_buff_percent = def_level * BUFF_LEVEL_TO_PERCENT_MULTIPLIER

                # シミュレーション実行時には属性バフは0として渡す (表計算用)
                # Pass attribute buffs as 0 during simulation execution (for table calculation)
                damages = run_multiple_simulations_for_params(
                    num_simulations, base_attack, base_spattack, base_defence, base_spdefence,
                    actual_atk_buff_percent, actual_def_buff_percent,
                    0, 0, # 属性バフは0として渡す / Pass attribute buffs as 0
                    selected_attack_subtype, selected_breakthrough_multiplier_rate, selected_attribute,
                    selected_attack_category_label,
                    memoria_aux_data_list, # 補助スキルデータ / Support skill data
                    st.session_state.legendary_per_attribute_totals, # レジェンダリー合計増幅データ / Legendary total amplification data
                    st.session_state.lily_role_selection, st.session_state.lily_role_correction_rate, # リリィ役職設定を渡す / Pass Lily role settings
                    st.session_state.lily_aux_prob_amp_per_attribute_totals, # リリィ補助スキル確率増幅を渡す / Pass Lily support skill probability amplification
                    st.session_state.selected_aux_prob_amp_element, # リリィ補助スキル確率増幅で選択された属性を渡す / Pass selected element for Lily support skill probability amplification
                    st.session_state.lily_attribute_selection, st.session_state.lily_attribute_correction_multiplier, # リリィ属性補正を渡す / Pass Lily element correction
                    st.session_state.charm_rates, st.session_state.global_order_rate, counter_rate, st.session_state.theme_rates, # order_rate は単一値 / order_rate is a single value
                    st.session_state.grace_active, neunwelt_active, # legion_match_active は True で固定 / legion_match_active is fixed to True
                    stack_meteor_active, stack_barrier_active,
                    critical_active,
                    st.session_state.opponent_costume_attribute, # 相手の衣装属性を渡す / Pass opponent costume element
                    st.session_state.opponent_costume_reduction_rate # 相手の衣装ダメージ軽減率を渡す / Pass opponent costume damage reduction rate
                )

                # 平均ダメージを計算
                # Calculate average damage
                average_damage = np.mean(damages)

                # 削ったHPの割合を計算
                # Calculate HP shaved percentage
                hp_shaved_percentage = min(100.0, max(0.0, (average_damage / target_hp) * 100))

                # 結果を辞書に格納 (一つのセルにまとめる)
                # Store results in a dictionary (combine into one cell)
                col_header_suffix = f" {def_level:+d}"
                row_data[f"防御バフ{col_header_suffix}"] = f"{int(round(average_damage)):,} ({hp_shaved_percentage:.1f}%)" # 四捨五入 / Round
            results_data.append(row_data)

        # 結果DataFrameを作成し表示
        # Create and display results DataFrame
        results_df = pd.DataFrame(results_data)

        # --- Styling modification starts here ---
        # Define a styling function for the first column
        def highlight_first_column(s):
            # Check if s is a pandas Series and its name is the new column header
            if isinstance(s, pd.Series) and s.name == "平均ダメ (HP割合)":
                # Apply background color #f8f9fb and text color #888888 (light grey)
                return ['background-color: #f8f9fb; color: #888888'] * len(s)
            return [''] * len(s)

        # Apply the styling to the DataFrame
        styled_results_df = results_df.style.apply(highlight_first_column, axis=0)
        st.dataframe(styled_results_df, use_container_width=True, hide_index=True)
        # --- Styling modification ends here ---

# --- ヒストグラムの出力 ---
# --- Histogram Output ---
st.subheader("詳細ダメージ計算") # Detailed Damage Calculation
st.write("特定の攻撃バフと防御バフでのダメージやダメージ分布を調べたい場合はこちら") # If you want to check damage and damage distribution with specific attack and defense buffs, click here.

# 属性攻撃バフ/防御バフの最大・最小値を計算
# base_attack, base_spattack, base_defence, base_spdefence はsidebarで定義されているのでアクセス可能
# Calculate max/min attribute attack/defense buffs
# base_attack, base_spattack, base_defence, base_spdefence are defined in the sidebar and accessible
max_attr_atk_buff = math.floor((base_attack + base_spattack) / 4)
min_attr_atk_buff = -max_attr_atk_buff
max_attr_def_buff = math.floor((base_defence + base_spdefence) / 4)
min_attr_def_buff = -max_attr_def_buff

col_hist1, col_hist2, col_hist3, col_hist4 = st.columns(4)
with col_hist1:
    hist_atk_level = st.slider(
        "攻撃バフ", # Attack Buff
        min_value=-20, max_value=20, value=0, step=1,
        key="hist_atk_buff_slider"
    )
with col_hist2:
    hist_attribute_atk_buff_value = st.slider(
        "属性攻撃バフ", # Attribute Attack Buff
        min_value=min_attr_atk_buff, max_value=max_attr_atk_buff, value=0, step=10000,
        key="hist_attr_atk_buff_slider"
    )
with col_hist3:
    hist_def_level = st.slider(
        "防御バフ", # Defense Buff
        min_value=-20, max_value=20, value=0, step=1,
        key="hist_def_buff_slider"
    )
with col_hist4:
    hist_attribute_def_buff_value = st.slider(
        "属性防御バフ", # Attribute Defense Buff
        min_value=min_attr_def_buff, max_value=max_attr_def_buff, value=0, step=10000,
        key="hist_attr_def_buff_slider"
    )

# ヒストグラム生成ボタン
# Histogram Generation Button
if st.button("シミュレーション実行", key="generate_histogram_button"): # Execute Simulation
    #memoria_aux_data_list の定義を追加
    # Add definition for memoria_aux_data_list
    memoria_aux_data_list = st.session_state.memoria_data.to_dict('records')

    # 実際のパーセンテージに変換
    # Convert to actual percentage
    hist_actual_atk_buff_percent = hist_atk_level * BUFF_LEVEL_TO_PERCENT_MULTIPLIER
    hist_actual_def_buff_percent = hist_def_level * BUFF_LEVEL_TO_PERCENT_MULTIPLIER

    # 指定されたバフで再度シミュレーションを実行してデータを取得
    # Run simulation again with specified buffs to get data
    hist_damages = run_multiple_simulations_for_params(
        num_simulations, base_attack, base_spattack, base_defence, base_spdefence,
        hist_actual_atk_buff_percent, hist_actual_def_buff_percent,
        hist_attribute_atk_buff_value, hist_attribute_def_buff_value, # 属性バフの値を渡す / Pass attribute buff values
        selected_attack_subtype, selected_breakthrough_multiplier_rate, selected_attribute,
        selected_attack_category_label,
        memoria_aux_data_list, # 補助スキルデータ / Support skill data
        st.session_state.legendary_per_attribute_totals, # レジェンダリー合計増幅データ / Legendary total amplification data
        st.session_state.lily_role_selection, st.session_state.lily_role_correction_rate, # リリィ役職設定を渡す / Pass Lily role settings
        st.session_state.lily_aux_prob_amp_per_attribute_totals, # リリィ補助スキル確率増幅を渡す / Pass Lily support skill probability amplification
        st.session_state.selected_aux_prob_amp_element, # リリィ補助スキル確率増幅で選択された属性を渡す / Pass selected element for Lily support skill probability amplification
        st.session_state.lily_attribute_selection, st.session_state.lily_attribute_correction_multiplier, # リリィ属性補正を渡す / Pass Lily element correction
        st.session_state.charm_rates, st.session_state.global_order_rate, counter_rate, st.session_state.theme_rates, # order_rate は単一値 / order_rate is a single value
        st.session_state.grace_active, neunwelt_active, # legion_match_active は True で固定 / legion_match_active is fixed to True
        stack_meteor_active, stack_barrier_active,
        critical_active,
        st.session_state.opponent_costume_attribute, # 相手の衣装属性を渡す / Pass opponent costume element
        st.session_state.opponent_costume_reduction_rate # 相手の衣装ダメージ軽減率を渡す / Pass opponent costume damage reduction rate
    )

    # Calculate standard bin width
    standard_bin_width = target_hp / 10

    # Determine the maximum value to display on the x-axis.
    max_damage_in_sims = np.max(hist_damages)

    # Calculate the upper limit for bins to cover max_damage_in_sims,
    # ensuring it's a multiple of standard_bin_width and at least one bin past target_hp.
    upper_limit_for_bins = max(max_damage_in_sims, target_hp + standard_bin_width)
    upper_limit_for_bins = math.ceil(upper_limit_for_bins / standard_bin_width) * standard_bin_width

    # Create uniformly spaced bins
    bins = np.arange(0, upper_limit_for_bins + standard_bin_width, standard_bin_width)
    # Ensure the first bin is exactly 0 if it's not already
    if bins[0] != 0:
        bins = np.insert(bins, 0, 0)

    # Matplotlibでヒストグラムを作成
    # Create histogram with Matplotlib
    fig, ax = plt.subplots(figsize=(12, 7))
    n, bins, patches = ax.hist(hist_damages, bins=bins, edgecolor='black', alpha=0.7)

    # HPの赤線
    # Red line for HP
    ax.axvline(target_hp, color='red', linestyle='dashed', linewidth=2, label=f'目標HP: {target_hp:,}') # Target HP

    # X軸の目盛り位置とラベルを設定
    # Set X-axis tick positions and labels
    xtick_positions = bins # All bin edges are tick positions
    xtick_labels = []

    # Generate labels for 0% to 100% and then "100%以上"
    # Generate labels for 0% to 100% and then "100% and above"
    first_over_100_percent_label_added = False
    for i, pos in enumerate(xtick_positions):
        if pos <= target_hp:
            # Labels for 0% to 100%
            percent_val = round(pos / target_hp * 100)
            xtick_labels.append(f"{percent_val:.0f}%")
        else:
            # For positions beyond 100%, only label the first one as "100%以上"
            # and subsequent ones as empty strings to avoid clutter
            # For positions beyond 100%, only label the first one as "100% and above"
            # and subsequent ones as empty strings to avoid clutter
            if not first_over_100_percent_label_added:
                xtick_labels.append("100%以上") # 100% and above
                first_over_100_percent_label_added = True
            else:
                xtick_labels.append("") # Subsequent ticks are blank

    ax.set_xticks(xtick_positions)
    ax.set_xticklabels(xtick_labels, rotation=45, ha='right')

    # Adjust limits to ensure all labels are visible and graph looks good
    ax.set_xlim(0, bins[-1]) # Set x-axis limit to the last bin edge

    ax.set_title(f"ダメージ分布 (攻撃バフ: {hist_atk_level}, 属性攻撃バフ: {hist_attribute_atk_buff_value:,}, "
                 f"防御バフ: {hist_def_level}, 属性防御バフ: {hist_attribute_def_buff_value:,})") # Damage Distribution (Attack Buff: ..., Attribute Attack Buff: ..., Defense Buff: ..., Attribute Defense Buff: ...)
    ax.set_xlabel("最終ダメージ (HP削り割合)") # Final Damage (HP Shaved Percentage)
    ax.set_ylabel("発生回数") # Occurrences
    ax.legend()
    ax.grid(axis='y', alpha=0.75)
    plt.tight_layout() # レイアウトを調整 / Adjust layout

    st.pyplot(fig) # Streamlitでヒストグラムを表示 / Display histogram in Streamlit

    # ヒストグラム表示条件での統計情報を出力
    # Output statistics for histogram display conditions
    st.write(f"--- 統計情報 (攻撃バフ: {hist_atk_level}, 属性攻撃バフ: {hist_attribute_atk_buff_value:,}, "
             f"防御バフ: {hist_def_level}, 属性防御バフ: {hist_attribute_def_buff_value:,}) ---") # --- Statistics (Attack Buff: ..., Attribute Attack Buff: ..., Defense Buff: ..., Attribute Defense Buff: ...) ---
    st.write(f"**最大ダメージ:** {np.max(hist_damages):,}") # Max Damage
    st.write(f"**最小ダメージ:** {np.min(hist_damages):,}") # Min Damage
    st.write(f"**平均ダメージ:** {round(np.mean(hist_damages)):,}") # Average Damage (rounded)

    # ヒストグラム表示部分でも「削ったHPの割合」を表示
    # Also display "HP shaved percentage" in the histogram display section
    hist_hp_shaved_percentage = min(100.0, max(0.0, (np.mean(hist_damages) / target_hp) * 100))
    st.write(f"**削ったHPの平均(%):** {hist_hp_shaved_percentage:.1f}%") # Average HP Shaved (%)

with st.expander("更新履歴・ダメージ計算式・要望,バグ報告", expanded=False): # Update History / Damage Calculation Formula / Requests, Bug Reports

    st.subheader("更新履歴") # Update History
    st.write("[Github](Githubのリンクを貼る)を参照してください。" # Please refer to [Github](Github link).
    )

    st.subheader("ダメージ計算式") # Damage Calculation Formula
    st.write("[Googleスプレッドシート](https://docs.google.com/spreadsheets/d/1t4myVGOMnsfyUcjqhMH3crammEVuG_HWclI1WJCV40g/edit?gid=2103497167)を参照してください。") # Please refer to [Google Spreadsheet].

    st.subheader("要望,バグ報告") # Requests, Bug Reports
    st.write("Discordまたはお題箱にて対応しています。  \n" + # Supported via Discord or suggestion box.
             "[Discord](Discordのリンクを貼る)(画像を送りたい場合,返信が欲しい場合はこちら)  \n" + # [Discord](Discord link) (For sending images or wanting a reply, click here)
             "[お題箱](お題箱のリンクを貼る)(匿名で送りたい場合はこちら)" # [Suggestion Box](Suggestion Box link) (For anonymous submissions, click here)
    )

with st.expander("免責事項", expanded=False): # Disclaimer
    st.write("本ツールのダメージ計算式は有志の検証から推測されたものであり、内容の正確性を保証するものではありません。  \n" + # The damage calculation formula in this tool is inferred from voluntary verification and does not guarantee the accuracy of its content.
             "本ツールの使用により生じた損害、損失について、作成者は一切の責任を負いかねます。  \n" + # The creator is not responsible for any damage or loss caused by the use of this tool.
             "作成者は内容の更新、修正、または利用に関する個別のサポートを行う義務を負いません。  \n" + # The creator is not obligated to provide individual support regarding content updates, corrections, or usage.
             "本ツールの内容や仕様は予告なく変更、削除される場合があります。あらかじめご了承ください。" # The content and specifications of this tool may be changed or deleted without prior notice. Please be aware of this in advance.
    )

# やることリスト
# To-do list
# ・簡易ダメシミュに、属性バフの説明入れる
# ・ダメージ処理の高速化(Numpy乱数による処理？)
# ・st.formで再実行を抑制
# ↓コードとは無関係
# ・ドメイン決める（lastbullet-damagesimulator）
# ・更新履歴（githubで書く）
# ・Discordサーバー立てる
# ・お題箱の準備
