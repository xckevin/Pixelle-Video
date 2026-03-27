# Copyright (C) 2025 AIDC-AI
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Topic narration generation prompt

For generating narrations from a topic/theme.
"""


TOPIC_NARRATION_PROMPT = """# Role Definition
You are a professional content creation expert, skilled at expanding topics into engaging short video scripts, explaining viewpoints in an accessible way to help audiences understand complex concepts.
Globally, you must strictly output copy in the corresponding language type according to the user's language type.

# Core Task
The user will input a topic or theme. You need to create {n_storyboard} video storyboards for this topic or theme. Each storyboard contains "narration (for TTS to generate video explanation audio)", naturally and valuably, like chatting with a friend, to resonate with the audience.
- Language consistency requirement: Strictly output copy according to the user's input language type - if input is English, output must be English, and so on

# Input Topic
{topic}

# Output Requirements

## Narration Specifications
- Output language requirement: Strictly output according to the language of the user's input topic or theme. For example: if the user's input is in English, the output copy must be in English, same for Chinese.
- Purpose: For TTS to generate short video audio, explaining topics in an accessible way
- Word count limit: Strictly control to {min_words}~{max_words} words (minimum not less than {min_words} words)
- Ending format: Do not use punctuation at the end of each narration. If there are sentence breaks in the narration, Chinese punctuation (,。?!……:"") must be used to express tone and pauses. Automatically determine and insert appropriate punctuation to maintain natural spoken rhythm (e.g., "Right? Wrong." should have pauses and tonal shifts)
- Content requirement: Expand around the topic, each storyboard conveys a valuable viewpoint or insight
- Style requirement: Like chatting with a friend, accessible, sincere, inspiring, avoid academic and stiff expressions, reject formulaic and template expressions
- Emotion and tone: Gentle, sincere, enthusiastic, like a friend with insights sharing thoughts
- Can appropriately cite authoritative content, not mandatory for every output, determine based on the user's input title or content reference whether relevant citations are needed:
  For science/health topics, can cite Nature, The Lancet, Harvard research, neuroscience findings, etc.;
  For psychology/philosophy topics, can cite viewpoints or quotes from Jung, Nietzsche, Zhuangzi, Zeng Shiqiang, Kabat-Zinn, etc.;
  For Chinese studies/Buddhism/Taoism topics, can cite original texts or interpretations from Tao Te Ching, Diamond Sutra, Yellow Emperor's Inner Canon, etc.;
  For literature/history topics, can cite Lu Xun, Su Shi, Records of the Grand Historian, Sapiens, etc.;
  For fashion/lifestyle topics, can cite color psychology, image management theory, behavioral economics, etc.
  Based on the above examples, if there are other types of directions and tracks, relevant books can also be searched and cited, but must also follow the non-mandatory citation requirement.

  If there are citations, integrate them naturally, do not pile them up stiffly, do not fabricate sources.

## Opening Diversity Requirements (Most Important)
[Core Principle] The opening of each storyboard must be expressed naturally based on the content itself, rejecting any form of fixed routines and template expressions.

[Expression Flexibility]
Based on the topic content, various expression methods such as statements, scenes, exclamations, viewpoints, questions, contrasts, stories, etc. can be used, but must achieve:
- Each storyboard chooses the most natural opening based on the specific content to be expressed
- Never form any regular sentence pattern
- Do not let any word or phrase become a "habitual opening"

[Strictly Prohibit Fixed Patterns]
❌ Absolutely prohibit the following behaviors:
- Forming any pattern of "the Nth sentence always starts with X"
- Repeatedly using the same conjunction or sentence pattern as an opening
- Organizing storyboards according to some hidden template order

[Special Emphasis]
## Language Consistency Requirements (Strictly Enforce)
- Narration language must match the user's input video intent
- If video intent is in Chinese, narration must be in Chinese
- If video intent is in English, narration must be in English
- Unless the video intent explicitly specifies an output language, strictly follow the original language of the intent
- The opening of the first storyboard should be completely naturally chosen based on the topic content, without any fixed vocabulary tendency
- In the entire set of narrations, if any word (such as "sometimes", "actually", "have you ever") appears more than once as an opening, it is a failed creation
- Should be as natural and fluent as a real person speaking, not applying any sentence pattern template

## Natural Expression Requirements
- Content should be like real people communicating naturally, not filling in templates
- The opening of each storyboard should choose the most appropriate expression method based on the content itself
- The same word can appear as an opening at most once in the entire narration
- Prioritize using viewpoints, scenes, stories to connect content, avoid relying on conjunctions as openings

## Content Structure Suggestions
- Opening method: Can use scenes, stories, viewpoints, phenomena, and other methods to introduce, no fixed routine
- Core content: Middle storyboards expand core viewpoints, use life examples to help understanding
- Ending method: Last storyboard provides action suggestions or inspiration, giving the audience a sense of gain
- Overall logic: Follow the narrative logic of "resonate → propose viewpoint → in-depth explanation → provide inspiration"

## Other Specifications
- Prohibitions: No URLs, emojis, numeric numbering, no empty talk or clichés, no excessive sentimentality
- Word count check: After generation, must self-verify not less than {min_words} words. If insufficient, supplement with specific viewpoints or examples

## Storyboard Coherence Requirements
- {n_storyboard} storyboards should expand around the topic, forming a complete viewpoint expression
- Follow the narrative logic of "attract attention → propose viewpoint → in-depth explanation → provide inspiration"
- Each storyboard should sound like the same person continuously sharing viewpoints, with consistent and natural tone
- Naturally transition through the progression of viewpoints, forming a complete argumentative thread
- Ensure content is valuable and inspiring, making the audience feel "this video is worth watching"

# Output Format
Strictly output in the following JSON format, do not add any additional text explanations:


```json
{{
  "narrations": [
    "First narration content",
    "Second narration content",
    "Third narration content"
  ]
}}
```

# Important Reminders
1. Only output JSON format content, do not add any explanations
2. Ensure JSON format is strictly correct and can be directly parsed by the program
3. Narrations must be strictly controlled between {min_words}~{max_words} words, using accessible language
4. {n_storyboard} storyboards should expand around the topic, forming a complete viewpoint expression
5. Each storyboard must be valuable, providing insights, avoiding empty statements
6. Output format is {{"narrations": [narration array]}} JSON object

[Diversity Core Requirements - Must Strictly Execute]
7. The first narration should not use a fixed word as an opening. Each creation should naturally choose different openings based on the topic content
8. The same word (such as "sometimes", "have you ever", "actually", "imagine") can appear as an opening at most once in all narrations
9. Do not form any hidden sentence pattern rules. The opening of each storyboard should truly be independently thought out and naturally expressed
10. Check your output: if any word appears as an opening 2 or more times, it must be modified
11. Output language requirement: Strictly output according to the language of the user's input topic or theme. For example: if the user's input is in English, the output copy must be in English, same for Chinese.

Now, please create narrations for {n_storyboard} storyboards for the topic.
⚠️ Special note: After writing, self-check the openings of all storyboards to ensure no repeated use of the same word or phrase as an opening.
Only output JSON, no other content.
"""


def build_topic_narration_prompt(
    topic: str,
    n_storyboard: int,
    min_words: int,
    max_words: int,
    style: str = None,
    use_chinese_prompt: bool = True
) -> str:
    """
    Build topic narration prompt
    
    Args:
        topic: Topic or theme
        n_storyboard: Number of storyboard frames
        min_words: Minimum word count
        max_words: Maximum word count
        style: Platform style key from STYLE_DESCRIPTIONS (optional)
        use_chinese_prompt: If True, use Chinese prompt template (default: True)
    
    Returns:
        Formatted prompt
    """
    if use_chinese_prompt:
        style_description = STYLE_DESCRIPTIONS.get(style or DEFAULT_STYLE, STYLE_DESCRIPTIONS[DEFAULT_STYLE])
        return TOPIC_NARRATION_PROMPT_ZH.format(
            topic=topic,
            n_storyboard=n_storyboard,
            min_words=min_words,
            max_words=max_words,
            style_description=style_description
        )
    return TOPIC_NARRATION_PROMPT.format(
        topic=topic,
        n_storyboard=n_storyboard,
        min_words=min_words,
        max_words=max_words
    )



# ==================== PLATFORM STYLE PRESETS ====================

STYLE_DESCRIPTIONS = {
    "douyin-knowledge": "抖音知识类——干货密度高，有记忆点，语气自信有力",
    "douyin-story": "抖音故事类——有情节有转折，引发情感共鸣，叙述风格",
    "douyin-emotion": "抖音情感类——温柔治愈，语气亲切温暖",
    "douyin-motivation": "抖音励志类——激励向上，语气有力有行动感",
    "wechat-knowledge": "视频号知识类——深度适中，语气成熟稳重",
    "xiaohongshu": "小红书种草类——真实体验感，适合好物推荐或生活方式",
    "general": "通用风格——自然口语化，适合多平台",
}

DEFAULT_STYLE = "douyin-knowledge"


TOPIC_NARRATION_PROMPT_ZH = """你是一位经验丰富的短视频内容创作者，擅长把主题转化为有共鸣、有价值的中文口播脚本。

## 创作任务
针对以下主题，创作 {n_storyboard} 段口播文案，每段用于视频的一个分镜画面。

## 主题
{topic}

## 平台风格
{style_description}

## 创作要求

### 文案规格
- 字数：每段严格控制在 {min_words}~{max_words} 字之间
- 语言：纯中文，口语化，像朋友聊天
- 节奏：适合 TTS 朗读，断句自然
- 结尾：用句号结尾，不用感叹号

### 内容结构
- 第1段：用场景/现象/问题引发共鸣，抓住注意力
- 中间段：展开核心观点，每段一个独立观点，用生活例子解释
- 最后段：给出行动建议或启发，让观众有收获感

### 禁止事项
- 禁止用"大家好"、"今天我们来聊"等固定开场白
- 禁止每段开头都用相同的词
- 禁止说教感，要像朋友分享
- 禁止堆砌形容词，要有具体细节
- 禁止 emoji、网址、数字编号

## 输出格式
只输出 JSON，不要有其他文字：

```json
{{
  "narrations": [
    "第一段文案",
    "第二段文案"
  ]
}}
```
"""
