| Tag                | Category | Label                  | Abstracted_Rationale                | DOC_Origin_Context             | Inference_Method                      |
| :----------------- | :------- | :--------------------- | :---------------------------------- | :----------------------------- | :------------------------------------ |
| psy:STM-CHAN-SMS   | STM      | SMS Channel            | Direct mobile text stimulus         | Telecom metadata; Message body | Message metadata parsing; NLP         |
| psy:STM-CHAN-EMAIL | STM      | Email Channel          | Email-based stimulus delivery       | Email headers; Email body      | Header analysis; NLP                  |
| psy:STM-CHAN-CALL  | STM      | Voice Call             | Auditory verbal stimulus            | Call metadata; Audio stream    | Speech-to-text; call pattern analysis |
| psy:STM-CHAN-SOC   | STM      | Social Channel         | Social media interaction stimulus   | Social platform APIs           | Engagement parsing; NLP               |
| psy:STM-CHAN-WEB   | STM      | Web Channel            | Website or landing page exposure    | Web analytics                  | Clickstream analysis                  |
| psy:STM-MOD-VIS    | STM      | Visual Modality        | Visual sensory input                | Images; UI; Video              | Computer vision; object detection     |
| psy:STM-MOD-AUD    | STM      | Auditory Modality      | Sound-based stimulus                | Audio streams                  | Signal processing; speech analysis    |
| psy:STM-MOD-TAC    | STM      | Tactile Modality       | Physical sensory input              | Device sensors                 | Haptic sensor analysis                |
| psy:STM-MSG-DIR    | STM      | Direct Message         | Explicit intent communication       | Text content                   | Intent classification NLP             |
| psy:STM-MSG-IND    | STM      | Indirect Message       | Ambient or contextual messaging     | Content feeds                  | Topic modeling                        |
| psy:STM-MSG-IMP    | STM      | Implicit Message       | Suggestive or metaphorical input    | Text; Media                    | Psycholinguistic inference            |
| psy:STM-SENT-POS   | STM      | Positive Tone          | Positive emotional framing          | Text; Media                    | Sentiment analysis                    |
| psy:STM-SENT-NEG   | STM      | Negative Tone          | Negative or fear-based framing      | Text; Media                    | Sentiment analysis                    |
| psy:STM-SENT-NEU   | STM      | Neutral Tone           | Factual or emotionally flat framing | Text                           | Sentiment neutrality scoring          |
| psy:STM-TRIG-HIGH  | STM      | High Trigger           | High emotional charge               | Text; Media                    | Keyword intensity scoring             |
| psy:STM-TRIG-MED   | STM      | Medium Trigger         | Moderate emotional charge           | Text                           | Arousal estimation                    |
| psy:STM-TRIG-LOW   | STM      | Low Trigger            | Low emotional charge                | Text                           | Arousal estimation                    |
| psy:STM-URG-IMM    | STM      | Immediate Urgency      | Requires immediate action           | Text                           | Temporal keyword detection            |
| psy:STM-URG-SOON   | STM      | Soon Urgency           | Near-term importance                | Text                           | Temporal expression recognition       |
| psy:STM-URG-LAT    | STM      | Low Urgency            | Long-term relevance                 | Text                           | Temporal expression recognition       |
| psy:STM-NOVEL-NEW  | STM      | Novel Exposure         | First-time exposure                 | User history                   | History comparison                    |
| psy:STM-NOVEL-REP  | STM      | Repeated Exposure      | Identical repeated input            | User history                   | Frequency analysis                    |
| psy:STM-NOVEL-VAR  | STM      | Variant Exposure       | Modified repetition                 | User history                   | Content diffing                       |
| psy:STM-FREQ-HIGH  | STM      | High Frequency         | Frequent exposure                   | Activity logs                  | Rate analysis                         |
| psy:STM-FREQ-MED   | STM      | Medium Frequency       | Moderate exposure                   | Activity logs                  | Rate analysis                         |
| psy:STM-FREQ-LOW   | STM      | Low Frequency          | Rare exposure                       | Activity logs                  | Rate analysis                         |
| psy:STM-SRC-HIGH   | STM      | High Trust Source      | Trusted sender                      | Social graph                   | Trust scoring                         |
| psy:STM-SRC-MED    | STM      | Medium Trust Source    | Moderately trusted sender           | Social graph                   | Trust scoring                         |
| psy:STM-SRC-LOW    | STM      | Low Trust Source       | Unknown or distrusted sender        | Social graph                   | Trust scoring                         |
| psy:ORI-CTRL       | ORI      | Control                | Desire to reduce uncertainty        | Behavior logs                  | Pattern rigidity analysis             |
| psy:ORI-FRE        | ORI      | Freedom                | Desire to preserve autonomy         | Choice data                    | Opt-out behavior analysis             |
| psy:ORI-ACH        | ORI      | Achievement            | Drive for mastery or proof          | Task systems                   | Goal completion tracking              |
| psy:ORI-SURV       | ORI      | Survival               | Threat avoidance orientation        | Risk data                      | Avoidance pattern modeling            |
| psy:ORI-CUR        | ORI      | Curiosity              | Exploration drive                   | Clickstream                    | Exploration entropy                   |
| psy:ORI-DEF        | ORI      | Defiance               | Resistance to authority             | Rule systems                   | Non-compliance analysis               |
| psy:ORI-VAL        | ORI      | Validation             | Need for approval                   | Social metrics                 | Engagement-seeking detection          |
| psy:ORI-ESC        | ORI      | Escape                 | Avoidance of discomfort             | Engagement logs                | Disengagement modeling                |
| psy:ORI-PAIN       | ORI      | Endurance              | Pain as identity                    | Text content                   | Self-referential hardship analysis    |
| psy:ORI-INT        | ORI      | Integrity              | Alignment with values               | Behavior consistency           | Value coherence analysis              |
| psy:ORI-EXCH       | ORI      | Exchange               | Reciprocity seeking                 | Transaction logs               | Reciprocal behavior detection         |
| psy:ORI-OBS        | ORI      | Observation            | Detached intake                     | Engagement metrics             | Passive consumption modeling          |
| psy:ORI-REB        | ORI      | Rebirth                | Identity reconstruction             | Behavior shifts                | Preference discontinuity detection    |
| psy:ORI-BND        | ORI      | Bonding                | Connection seeking                  | Social graph                   | Network interaction density           |
| psy:ORI-DISC       | ORI      | Discovery              | Truth-seeking                       | Content depth                  | Topic deep-dive analysis              |
| psy:ORI-CTRLIN     | ORI      | Inner Control          | Self-regulation                     | Correction logs                | Self-modulation detection             |
| psy:ORI-EXP        | ORI      | Expression             | Externalization of inner state      | Content creation               | Expressive output analysis            |
| psy:ORI-DYN        | ORI      | Dynamism               | Preference for motion               | Interaction tempo              | Activity velocity                     |
| psy:ORI-ORD        | ORI      | Order                  | System construction drive           | Content structure              | Organization pattern analysis         |
| psy:ORI-RISK       | ORI      | Risk                   | Uncertainty pursuit                 | Financial actions              | Risk exposure modeling                |
| psy:ORI-GROW       | ORI      | Growth                 | Self-expansion                      | Learning logs                  | Skill acquisition tracking            |
| psy:ORI-SERV       | ORI      | Service                | Other-oriented action               | Pro-social actions             | Altruism signal detection             |
| psy:ORI-HARM       | ORI      | Harmony                | Conflict avoidance                  | Interaction tone               | Conflict minimization analysis        |
| psy:ORI-TIME       | ORI      | Legacy                 | Time-extended meaning               | Content persistence            | Temporal projection modeling          |
| psy:ORI-SYNC       | ORI      | Synchronization        | Rhythm alignment                    | Activity cycles                | Temporal pattern analysis             |
| psy:ORI-FEAR       | ORI      | Fear Orientation       | Threat-focused worldview            | Risk logs                      | Threat salience modeling              |
| psy:THT-RSN-DEDUCT | THT      | Deductive Reasoning    | General to specific logic           | Text                           | Logical structure parsing             |
| psy:THT-RSN-INDUCT | THT      | Inductive Reasoning    | Pattern generalization              | Text                           | Pattern abstraction                   |
| psy:THT-RSN-ABDUCT | THT      | Abductive Reasoning    | Best-guess inference                | Text                           | Hypothesis ranking                    |
| psy:THT-META-AWARE | THT      | Metacognition          | Awareness of thinking               | Text                           | Metacognitive marker detection        |
| psy:THT-LOAD-HIGH  | THT      | High Load              | Cognitive overload                  | Behavior logs                  | Task switching analysis               |
| psy:THT-LOAD-MED   | THT      | Medium Load            | Moderate effort                     | Behavior logs                  | Interaction complexity                |
| psy:THT-LOAD-LOW   | THT      | Low Load               | Automatic processing                | Behavior logs                  | Response latency                      |
| psy:EMO-ANX        | EMO      | Anxiety                | Anticipated threat                  | Physiology; Text               | HRV variance; sentiment               |
| psy:EMO-FEAR       | EMO      | Fear                   | Acute danger response               | News; Physiology               | Threat detection                      |
| psy:EMO-HOPE       | EMO      | Hope                   | Positive future projection          | Text                           | Future-oriented language              |
| psy:EMO-PRIDE      | EMO      | Pride                  | Identity satisfaction               | Social media                   | Self-reference + engagement           |
| psy:EMO-STRES      | EMO      | Stress                 | Overload response                   | Physiology                     | Arousal saturation                    |
| psy:EMO-JOY        | EMO      | Joy                    | Positive fulfillment                | Physiology; Media              | Positive affect detection             |
| psy:EMO-ANGER      | EMO      | Anger                  | Boundary violation response         | Text; Video                    | Sentiment intensity                   |
| psy:BEH-AVD        | BEH      | Avoidance              | Disengagement behavior              | Engagement logs                | Exit pattern analysis                 |
| psy:BEH-ENG        | BEH      | Engagement             | Active interaction                  | Interaction logs               | Participation detection               |
| psy:BEH-INIT       | BEH      | Initiative             | Self-starting action                | Task logs                      | Unprompted action detection           |
| psy:BEH-CHAL       | BEH      | Challenge              | Norm confrontation                  | Rule systems                   | Violation analysis                    |
| psy:BEH-EXPR       | BEH      | Expression             | Externalized state                  | Content creation               | Output analysis                       |
| psy:HAB-RPT        | HAB      | Repetition             | Unquestioned recurrence             | Time-series logs               | Behavior recurrence detection         |
| psy:HAB-NEG        | HAB      | Negative Loop          | Self-reinforcing harm               | Longitudinal logs              | Outcome deterioration analysis        |
| psy:HAB-POS        | HAB      | Positive Reinforcement | Reward-maintained behavior          | Outcome feedback               | Reinforcement signal detection        |
| psy:HAB-CTRL       | HAB      | Control Routine        | Anxiety-reducing structure          | Routine logs                   | Predictability modeling               |
| psy:HAB-ESC        | HAB      | Escape Habit           | Avoidant repetition                 | Engagement logs                | Repeated disengagement                |
| psy:OUT-CONV       | OUT      | Conversion             | Desired action achieved             | Transaction logs               | Goal completion confirmation          |
| psy:OUT-REJ        | OUT      | Rejection              | Active refusal                      | Interaction logs               | Opt-out detection                     |
| psy:OUT-OPEN       | OUT      | Open                   | Acknowledgment only                 | Message logs                   | Open event detection                  |
| psy:OUT-IGN        | OUT      | Ignore                 | No interaction                      | Delivery logs                  | Null response detection               |
| psy:OUT-TRUST      | OUT      | Trust                  | Increased compliance                | Longitudinal behavior          | Trust delta modeling                  |
| psy:OUT-SAT        | OUT      | Satisfaction           | Positive resolution                 | Post-action data               | Positive outcome inference            |
| psy:OUT-BRK        | OUT      | Break                  | Pattern anomaly                     | Behavior baselines             | Deviation detection                   |
| psy:OUT-DORM       | OUT      | Dormant                | Prolonged inactivity                | Activity logs                  | Silence duration modeling             |

CSV Form: [[Psy-Chart.csv]]