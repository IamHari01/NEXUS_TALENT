from sentence_transformers import CrossEncoder


class ATSCrossEncoder:
    def __init__(self):
        self.model = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")


    def score(self, resume, jd):
        return int(self.model.predict([(resume, jd)])[0] * 100)