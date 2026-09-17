"""Public workspace integration: synthetic sources and decisions only."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

TOOL = Path(__file__).resolve().parents[1]

class WorkspaceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        (self.root/'raw').mkdir()
        (self.root/'sessions').mkdir()
        (self.root/'raw/policy.md').write_text('Return within 14 days.\n')
        self.config = self.root/'wiki.toml'
        self.config.write_text('[wiki]\npath="knowledge"\ntitle="Team Wiki"\nreviewer="human:alice"\n[sources.notes]\nkind="documents"\npath="raw"\n[sources.claude-sessions]\nkind="claude"\npath="sessions"\n')
        self.env = {k:v for k,v in os.environ.items() if not k.startswith('WIKI_')}
        self.env.update(WIKI_CONFIG=str(self.config), PYTHONDONTWRITEBYTECODE='1')

    def run_tool(self, script, *args, ok=True):
        result = subprocess.run([sys.executable,'-B',str(TOOL/'scripts'/script),*args],env=self.env,cwd=self.root,capture_output=True,text=True)
        if ok: self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        return result

    def prepare(self):
        self.run_tool('setup.py')
        draft=self.root/'draft';draft.mkdir()
        (draft/'concepts').mkdir()
        body='---\ntype: concept\ntitle: Returns\ndescription: Return window\nverified: []\n---\nReturn within 14 days. ^[/notes/policy.md:1]\n'
        (draft/'concepts/returns.md.txt').write_text(body)
        card={'title':'Return policy','summary':'Initial policy','files':['concepts/returns.md'],'judgments':[{'kind':'fact','before':'No wiki','proposed':'14 days','reason':'Policy document','evidence':['^[/notes/policy.md:1]']}]}
        cp=self.root/'card.json';cp.write_text(json.dumps(card))
        out=self.run_tool('review.py','prepare','first','returns','--card',str(cp),'--draft-dir',str(draft))
        return json.loads(out.stdout)['revision']

    def approve(self,revision,role='user',by='human:alice'):
        (self.root/'sessions/decision.jsonl').write_text(json.dumps({'type':role,'message':{'content':'Approve the reviewed change.'}})+'\n')
        rp=self.root/'response.json'
        rp.write_text(json.dumps({'by':by,'quote':'Approve the reviewed change.','evidence':'^[/claude-sessions/decision.jsonl:1]'}))
        return self.run_tool('review.py','decide','first','returns','--revision',revision,'--decision','approved','--response',str(rp),ok=False)

    def test_setup_idempotent_preserves_human_files_and_links(self):
        (self.root/'AGENTS.md').write_text('Existing project instructions\n')
        self.run_tool('setup.py')
        schema=self.root/'knowledge/SCHEMA.md';schema.write_text('My edited rules\n')
        config=self.config.read_bytes()
        self.run_tool('setup.py')
        self.assertEqual(schema.read_text(),'My edited rules\n')
        self.assertEqual(config,self.config.read_bytes())
        instructions=(self.root/'AGENTS.md').read_text()
        self.assertTrue(instructions.startswith('Existing project instructions'))
        self.assertEqual(instructions.count('<!-- llm-wiki -->'),1)
        for provider in ['.claude','.agents']:
            self.assertEqual(len(list((self.root/provider/'skills').iterdir())),4)
            self.assertEqual((self.root/provider/'skills/wiki-review').resolve(),TOOL/'skills/wiki-review')
        self.assertIn('Team Wiki',(self.root/'knowledge/index.md').read_text())
        self.assertNotIn('Clippings',self.run_tool('lint.py').stdout)

    def test_configured_alias_reviewer_and_full_public_workflow(self):
        revision=self.prepare()
        preview=self.run_tool('review.py','preview','first','returns').stdout
        self.assertIn('0 errors',preview)
        denied=self.run_tool('review.py','apply','first','returns',ok=False)
        self.assertNotEqual(denied.returncode,0)
        self.assertEqual(self.approve(revision).returncode,0)
        self.run_tool('review.py','apply','first','returns')
        root=self.root/'knowledge'
        receipt=(root/'reviews/first/applied.jsonl').read_bytes()
        self.run_tool('review.py','apply','first','returns')
        self.assertEqual(receipt,(root/'reviews/first/applied.jsonl').read_bytes())
        self.assertTrue((root/'concepts/returns.md').exists())
        self.assertIn('[[concepts/returns', (root/'index.md').read_text())
        self.run_tool('lint.py')

    def test_wrong_reviewer_and_assistant_evidence_rejected(self):
        rev=self.prepare()
        self.assertNotEqual(self.approve(rev,by='human:bob').returncode,0)
        self.assertNotEqual(self.approve(rev,role='assistant').returncode,0)

    def test_human_edit_after_prepare_is_preserved(self):
        rev=self.prepare()
        self.assertEqual(self.approve(rev).returncode,0)
        page=self.root/'knowledge/concepts/returns.md';page.write_text('Human edited this in Obsidian.\n')
        result=self.run_tool('review.py','apply','first','returns',ok=False)
        self.assertNotEqual(result.returncode,0)
        self.assertEqual(page.read_text(),'Human edited this in Obsidian.\n')

    def test_registered_sources_all_required_even_same_kind(self):
        self.config.write_text(self.config.read_text()+'\n[sources.second]\nkind="documents"\npath="other"\n')
        record={'version':1,'period':{'from':'2026-01-01T00:00:00Z','through':'2026-02-01T00:00:00Z'},'basis':{'last_apply':'none','last_full_review':'unknown; first run'},'sources':[{'id':alias,'kind':kind,'location':alias,'status':'scanned','reason':'read and compared','items':[]} for alias,kind in [('notes','documents'),('claude-sessions','claude')]]}
        p=self.root/'inventory.json';p.write_text(json.dumps(record))
        result=self.run_tool('inventory.py',str(p),'--require-complete',ok=False)
        self.assertEqual(result.returncode,1)
        self.assertIn('second',result.stdout)
        record['sources'].append({'id':'second','kind':'documents','location':'other','status':'unavailable','reason':'missing folder','items':[]})
        p.write_text(json.dumps(record))
        self.assertEqual(self.run_tool('inventory.py',str(p),'--require-complete',ok=False).returncode,2)

    def test_clippings_unconfigured_fails_explicitly(self):
        result=self.run_tool('clippings_todo.py','--all',ok=False)
        self.assertEqual(result.returncode,2)
        self.assertIn('Configure',result.stderr)

    def test_missing_explicit_configuration_fails(self):
        self.config.unlink()
        self.assertNotEqual(self.run_tool('lint.py',ok=False).returncode,0)

    def test_wiki_outside_workspace_rejected(self):
        self.config.write_text('[wiki]\npath="../outside-wiki"\n')
        self.assertNotEqual(self.run_tool('setup.py',ok=False).returncode,0)
