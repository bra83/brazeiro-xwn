import re

class NarrativePolicy:
    SCENE_GRAMMAR=(
        'CONTEXTO → ESPAÇO → MOVIMENTO → FOCO → IMPLICAÇÃO → ABERTURA PARA AÇÃO',
        'PANORAMA → LOCAL → PERSONAGENS/OBJETOS → DETALHE MARCANTE',
        'PERCEPTÍVEL → OBSERVÁVEL → INFERÍVEL → OCULTO',
        'SINAL → DESCOBERTA → CONSEQUÊNCIA → NOVA PERGUNTA',
    )
    TRAVEL_GRAMMAR=('procedure','relevant_result','consequence','new_decision')
    COMBAT_GRAMMAR=('threat','movement','trajectory','contact','result','consequence')
    FAILURE_MODES=('cost','exposure','time','position','complication')
    DIRECTIVES={
        'compress_routine_when_unchanged':True,'reexpand_travel_on_new_decision':True,
        'world_already_moving':True,'npc_has_current_activity':True,'npc_knowledge_is_limited':True,
        'rumor_is_not_truth':True,'revisit_preserves_known_geometry':True,'threat_is_signaled_before_contact':True,
        'avoid_npc_monologues':True,'answer_all_relevant_questions':True,'stop_at_first_meaningful_uncertainty':True,
        'checks_only_for_meaningful_uncertainty':True,'basic_conversation_needs_no_social_check':True,
        'essential_clue_never_single_roll_gate':True,'planning_and_meta_freeze_fiction':True,'rules_outside_narrative':True,
        'tts_only_narrative_and_dialogue':True,'memory_truth_separate_from_presentation':True,
        'player_character_control_is_human_only':True,'end_scene_on_meaningful_decision':True,
        'avoid_ornamental_prose':True,'table_voice':True,'anti_summary':True,
    }
    _META_PATTERNS=(r'^\s*(regra|regras|rules?)\b',r'^\s*(como funciona|how does .* work)\b',r'^\s*(fora do jogo|meta\b|ooc\b)',r'^\s*(posso perguntar|dúvida)\b')
    _PLANNING_PATTERNS=(r'^\s*(planejo|planejamos|quero planejar|vamos planejar)\b',r'^\s*(i plan|we plan|let.?s plan)\b')
    _TRAVEL_WORDS=('viajo','viajar','estrada','trilha','jornada','atravesso','travel','journey','road','trail','cross the')
    _COMBAT_WORDS=('ataco','ataque','golpeio','disparo','combate','luto','attack','shoot','strike','fight')
    _DIALOGUE_WORDS=('pergunto','digo','falo','converso','respondo','ask ','tell ','say ','speak ','talk ')
    _INVESTIGATION_WORDS=('investigo','examino','procuro','vasculho','observo','inspeciono','investigate','examine','search','inspect')
    _DELIBERATIVE=(r'\bconsidero\b',r'\bpenso em\b',r'\btalvez\b',r'\bquem sabe\b',r'\bi consider\b',r'\bi think about\b',r'\bmaybe\b',r'\bperhaps\b')
    _FORCED_ACTION_PATTERNS=(
        r'\bvocê\s+(abre|ataca|mata|pega|entra|vai|aceita|pula|corre|dispara|empurra|usa)\b',
        r'\byou\s+(open|attack|kill|take|enter|go|accept|jump|run|shoot|push|use)\b',
    )
    def classify(self,text):
        low=str(text).strip().lower()
        if any(re.search(p,low,re.I) for p in self._META_PATTERNS): return 'meta'
        if any(re.search(p,low,re.I) for p in self._PLANNING_PATTERNS): return 'planning'
        return 'fiction'
    def fiction_kind(self,text):
        low=str(text).lower()
        if any(w in low for w in self._COMBAT_WORDS): return 'combat'
        if any(w in low for w in self._TRAVEL_WORDS): return 'travel'
        if any(w in low for w in self._DIALOGUE_WORDS) or '?' in low: return 'dialogue'
        if any(w in low for w in self._INVESTIGATION_WORDS): return 'investigation'
        return 'action'
    def advances_world(self,text): return self.classify(text)=='fiction'
    def target_chars(self,importance='normal'):
        bands={'routine':(180,450),'normal':(350,900),'meaningful':(700,1800),'climax':(1200,3200)}
        if importance not in bands: raise ValueError('invalid_importance')
        return bands[importance]
    def minimum_acceptable_chars(self,importance='normal'):
        low,_=self.target_chars(importance)
        return int(low*0.6) if importance in {'meaningful','climax'} else 1
    def question_count(self,text):
        s=str(text); explicit=s.count('?')
        if explicit: return explicit
        starters=re.findall(r'(?i)\b(quem|qual|quais|quando|onde|por que|porque|como|what|who|when|where|why|how)\b',s)
        return len(starters)
    def social_check_needed(self,text,meaningful_uncertainty=False):
        if not isinstance(meaningful_uncertainty,bool): raise ValueError('invalid_uncertainty_flag')
        if not meaningful_uncertainty: return False
        low=str(text).lower(); basic=any(x in low for x in ['qual seu nome','como você se chama','what is your name','onde fica','where is'])
        return not basic
    def turn_plan(self,text,mechanical=False,importance='normal'):
        if not isinstance(mechanical,bool): raise ValueError('invalid_mechanical_flag')
        self.target_chars(importance)
        mode=self.classify(text); kind='meta' if mode=='meta' else ('planning' if mode=='planning' else self.fiction_kind(text))
        qcount=self.question_count(text)
        meaningful_uncertainty=bool(mechanical and mode=='fiction')
        basic_social=(kind=='dialogue' and not self.social_check_needed(text,meaningful_uncertainty))
        check_required=bool(meaningful_uncertainty and not basic_social)
        channels={
            'narrative': mode=='fiction',
            'rules': mode=='meta',
            'help': mode in {'meta','planning'},
            'tts': mode=='fiction',
        }
        procedure=None
        if kind=='travel': procedure=list(self.TRAVEL_GRAMMAR)
        elif kind=='combat': procedure=list(self.COMBAT_GRAMMAR)
        return {
            'mode':mode,'kind':kind,'world_advances':mode=='fiction','question_count':qcount,
            'meaningful_uncertainty':meaningful_uncertainty,'check_required':check_required,
            'failure_modes':list(self.FAILURE_MODES) if check_required else [],
            'essential_clue_protected':kind=='investigation',
            'stop_condition':'first_meaningful_uncertainty' if check_required else 'meaningful_decision',
            'procedure':procedure,'channels':channels,
            'target_chars':list(self.target_chars(importance)),
        }
    def narrator_directives(self,importance='normal',question_count=0,turn_plan=None):
        out={'directives':dict(self.DIRECTIVES),'scene_grammar':list(self.SCENE_GRAMMAR),'failure_modes':list(self.FAILURE_MODES),'target_chars':list(self.target_chars(importance)),'question_count':question_count}
        if turn_plan is not None: out['turn_plan']=turn_plan
        return out
    def validate_player_agency(self,user_text,narration):
        low=str(user_text).lower(); rendered=str(narration).lower()
        deliberative=any(re.search(p,low,re.I) for p in self._DELIBERATIVE)
        if deliberative and any(re.search(p,rendered,re.I) for p in self._FORCED_ACTION_PATTERNS):
            raise ValueError('player_agency_violation')
        return True
