class RequestHandler:
    def __init__(self, template_mgr: TemplateManager, nlp_processor: PurposeAnalyzer):
        self.template_mgr = template_mgr
        self.nlp = nlp_processor
    
    async def handle_request(self, request_data: dict) -> ExecutionTemplate:
        """Handle request with validation and fallback"""
        self._validate_request(request_data)
        
        if 'purpose_id' not in request_data:
            request_data['purpose_id'] = self.nlp.determine_purpose(request_data['text'])
            if not request_data['purpose_id']:
                raise ValueError("Unable to determine request purpose")
        
        return self.template_mgr.get_template(request_data['purpose_id'])
    
    def _validate_request(self, request_data: dict):
        """Basic request validation"""
        if not request_data.get('text'):
            raise ValueError("Request must contain text content") 