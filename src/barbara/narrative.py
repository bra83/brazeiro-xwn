import re

class NarrativePolicy:
    SCENE_GRAMMAR=(
        'CONTEXTO → ESPAÇO → MOVIMENTO → FOCO → IMPLICAÇÃO → ABERTURA PARA AÇÃO',
        'PANORAMA → LOCAL → PERSONAGENS/OBJETOS → DETALHE MARCANTE',
        'PERCEPTÍVEL → OBSERVÁVEL → INFERÍVEL → OCULTO',
        'SINAL → DESCOBERTA → CONSEQUÊNCIA → NOVA PERGUNTA',
    )
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
    def classify(self,text):
        low=str(text).strip().lower()
        if any(re.search(p,low,re.I) for p in self._META_PATTERNS): return 'meta'
        if any(re.search(p,low,re.I) for p in self._PLANNING_PATTERNS): return 'planning'
        return 'fiction'
    def advances_world(self,text): return self.classify(text)=='fiction'
    def target_chars(self,importance='normal'):
        bands={'routine':(180,450),'normal':(350,900),'meaningful':(700,1800),'climax':(1200,3200)}
        if importance not in bands: raise ValueError('invalid_importance')
        return bands[importance]
    def minimum_acceptable_chars(self,importance='normal'):
        low,_=self.target_chars(importance)
        return int(low*0.6) if importance in {'meaningful','climax'} else 1
    def question_count(self,text):
        s=str(text)
        explicit=s.count('?')
        if explicit: return explicit
        starters=re.findall(r'(?i)\b(quem|qual|quais|quando|onde|por que|porque|como|what|who|when|where|why|how)\b',s)
        return len(starters)
    def narrator_directives(self,importance='normal',question_count=0):
        return {'directives':dict(self.DIRECTIVES),'scene_grammar':list(self.SCENE_GRAMMAR),'failure_modes':list(self.FAILURE_MODES),'target_chars':list(self.target_chars(importance)),'question_count':question_count}
    def social_check_needed(self,text,meaningful_uncertainty=False):
        if not isinstance(meaningful_uncertainty,bool): raise ValueError('invalid_uncertainty_flag')
        if not meaningful_uncertainty: return False
        low=str(text).lower(); basic=any(x in low for x in ['qual seu nome','como você se chama','what is your name','onde fica','where is'])
        return not basic
