# patient-routing-system

## Workflow
1. User sends the symptoms to the system.
2. API validates the request.
3. ConversationManager retrieves context.
4. LLM extracts structured symptoms data.
5. SymptomNormalizer standardizes the terms.
6. SafetyEngine checks emergency conditions.
7. System determines if follow-up questions are needed.
8. TriageClassifier generates a classification.
9. Department recommendation is made based on classification.
10. Final response is returned.
11. Session logs persisted for future reference.

# Overview
The Patient Routing System is designed to assist healthcare providers in efficiently directing patients to the appropriate departments based on their symptoms. The system leverages natural language processing (NLP) and machine learning techniques to analyze patient input, extract relevant information, and make informed routing decisions.
