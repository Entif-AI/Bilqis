"""Grow actual acquired representations into a larger network without reset."""
import random
import unittest

from bilqis_active import load_active
from bilqis_school.arithmetic import extend_graph
from bilqis_school.lessons import TeacherLibrary,compose_batch,encode
from bilqis_school.grow import grow,compare_outputs
from bilqis_development.continuation import expand
from bilqis_ref.model import batch,state_hash
from bilqis_micro.run import optimizer_receipt


class PreserveAcquiredStudent(unittest.TestCase):
    def test_wider_deeper_student_preserves_existing_answers_and_adamw(self):
        old,opt,payload,_=load_active()
        graph=extend_graph(payload["graph"])
        expand(old,opt,payload["graph"],graph)
        old_hash=state_hash(old)
        old_step=optimizer_receipt(opt)["steps"]
        larger,new_optimizer,report=grow(old,opt,factor=2,layers=4)
        self.assertGreater(report["new_parameters"],report["old_parameters"])
        self.assertEqual(old_step,optimizer_receipt(new_optimizer)["steps"])
        self.assertEqual(old_hash,state_hash(old))
        library=TeacherLibrary()
        tests=[]
        for grade in (1,10,17,19,22):
            policy={"old":12,"preview":2,"depth":2,"contrast":1.,
                    "lr":.00013,"distill":.35}
            records,_=compose_batch(library,grade,policy,graph,random.Random(grade))
            tests.append(batch([encode(row,graph) for row in records]))
        results=compare_outputs(old,larger,tests)
        self.assertEqual(results["preserved_examples"],5*32)
        self.assertLess(results["max_logit_absolute_difference"],3e-4)
        self.assertEqual(larger.config.width,192)
        self.assertEqual(larger.config.layers,4)
        self.assertEqual(larger.config.vocab_size,222)


if __name__=="__main__":
    unittest.main()
