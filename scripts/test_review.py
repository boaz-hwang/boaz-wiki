"""Human review gates exercised on isolated repositories; never publish fixture decisions."""
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import review
import wikilib


def page(title, body="text", extra=""):
    return f"---\ntype: concept\ntitle: {title}\ndescription: {title} summary\nverified: []\n{extra}---\n{body}\n".encode()


class ReviewTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = Path(self.tmp.name).resolve()
        self.wiki = self.repo / 'docs/wiki'
        self.wiki.mkdir(parents=True)
        self.r = review.Review(self.wiki, self.repo)
        self.raw = self.repo / 'raw.md'
        self.raw.write_text('actual evidence\nsecond line\n', encoding='utf-8')
        self.sessions = self.repo / 'sessions'
        self.sessions.mkdir()
        self.record({'type':'user','message':{'content':'검토한 범위로 승인합니다'}})
        self.addCleanup(patch.stopall)
        patch.dict(review.EXTRA_ROOTS, {'claude-sessions':self.sessions, 'codex-sessions':self.sessions}).start()
        patch.dict(os.environ, {'WIKI_CLAUDE_SESSIONS_DIR':str(self.sessions), 'WIKI_CODEX_SESSIONS_DIR':str(self.sessions), 'WIKI_CLIPPINGS_DIR':str(self.repo/'no-clips')}).start()
        self.response = {'by':'human:owner','quote':'검토한 범위로 승인합니다','evidence':'^[/claude-sessions/user.jsonl:1]'}
        self.put('concepts/a.md', page('a', 'old'))

    def record(self, row):
        (self.sessions/'user.jsonl').write_text(json.dumps(row, ensure_ascii=False)+'\n', encoding='utf-8')

    def put(self, rel, data):
        p = self.wiki/rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)

    def prepare(self, topic='one', files=None, **kwargs):
        files = files or {'concepts/a.md':page('a','new ^[/raw.md:1]')}
        draft = self.repo/('draft-'+topic)
        draft.mkdir(exist_ok=True)
        for rel, data in files.items():
            p = draft/(rel+".txt")
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(data)
        card = {'title':topic,'summary':'Review change and its scope','files':list(files),
                'judgments':[{'kind':'interpretation','before':'old','proposed':'new','reason':'evidence','evidence':['^[/raw.md:1]']}], **kwargs}
        return self.r.prepare('batch',topic,card,draft)

    def approve(self, result, state='approved'):
        return self.r.decide('batch',result['topic'],result['revision'],state,self.response)

    def test_prepare_isolated_and_excluded_from_readers(self):
        result = self.prepare()
        self.assertEqual((self.wiki/'concepts/a.md').read_bytes(),page('a','old'))
        self.assertIn('-old',Path(result['review']).read_text(encoding='utf-8'))
        self.put('reviews/bad.md',b'[[does-not-exist]]')
        with patch.object(wikilib,'WIKI_ROOT',self.wiki):
            self.assertEqual(list(wikilib.iter_pages()),[self.wiki/'concepts/a.md'])
        output = self.r.preview('batch',['one'])[3]
        self.assertIn('1 pages · 0 errors',output)
        self.assertNotIn('bad.md',output)

    def test_all_nonapproved_states_block_apply(self):
        result = self.prepare()
        for state in [None,'deferred','rejected','changes_requested']:
            if state: self.approve(result,state)
            with self.assertRaisesRegex(ValueError,'사람 승인 없음'):
                self.r.apply('batch',['one'])
        self.assertEqual((self.wiki/'concepts/a.md').read_bytes(),page('a','old'))

    def test_exact_approval_apply_receipt_and_idempotence(self):
        result = self.prepare()
        self.approve(result)
        self.assertIn('반영 완료',self.r.apply('batch',['one']))
        snapshot={p:p.read_bytes() for p in self.wiki.rglob('*') if p.is_file()}
        self.assertIn('이미 반영',self.r.apply('batch',['one']))
        self.assertEqual(snapshot,{p:p.read_bytes() for p in self.wiki.rglob('*') if p.is_file()})
        self.assertIn('review-apply',(self.wiki/'log.md').read_text(encoding='utf-8'))
        self.assertFalse(wikilib.parse_frontmatter((self.wiki/'concepts/a.md').read_text(encoding='utf-8'))[0]['verified'])
        self.assertEqual(self.r.status()['batch'][0]['state'],'applied')

    def test_only_selected_approved_topic_is_applied(self):
        a=self.prepare(); b=self.prepare('two',{'concepts/b.md':page('b')})
        self.approve(a); self.approve(b)
        self.r.apply('batch',['two'])
        self.assertEqual((self.wiki/'concepts/a.md').read_bytes(),page('a','old'))
        self.assertTrue((self.wiki/'concepts/b.md').exists())
        self.r.apply('batch',['one'])

    def test_model_and_tool_cannot_supply_approval(self):
        result=self.prepare()
        for row in [
            {'type':'assistant','message':{'content':self.response['quote']}},
            {'type':'user','message':{'content':[{'type':'tool_result','content':self.response['quote']}]}},
            {'type':'attachment','attachment':{'type':'queued_command','prompt':self.response['quote'],'origin':{'kind':'agent'}}},
        ]:
            self.record(row)
            with self.assertRaisesRegex(ValueError,'사용자 메시지에 없음'): self.approve(result)

    def test_claude_queued_and_codex_messages_supported(self):
        for row in [
            {'type':'attachment','attachment':{'type':'queued_command','prompt':self.response['quote'],'origin':{'kind':'human'}}},
            {'type':'response_item','payload':{'type':'message','role':'user','content':[{'type':'input_text','text':self.response['quote']}]}},
            {'type':'event_msg','payload':{'type':'user_message','message':self.response['quote']}},
        ]:
            self.record(row)
            self.assertIsNotNone(self.r.user_evidence(self.response))

    def test_session_append_does_not_invalidate(self):
        result=self.prepare(dependencies=[self.response['evidence']]); self.approve(result)
        with (self.sessions/'user.jsonl').open('a') as f: f.write(json.dumps({'type':'metadata'})+'\n')
        self.r.apply('batch',['one'])

    def test_user_evidence_mutation_blocks_apply(self):
        result=self.prepare(); self.approve(result)
        self.record({'type':'user','message':{'content':self.response['quote']+' but changed'}})
        with self.assertRaisesRegex(ValueError,'승인 원문 변경'): self.r.apply('batch',['one'])

    def test_new_revision_invalidates_only_that_topic(self):
        a=self.prepare(); b=self.prepare('two',{'concepts/b.md':page('b')})
        self.approve(a); self.approve(b)
        newer=self.prepare(files={'concepts/a.md':page('a','revised')})
        self.assertNotEqual(a['revision'],newer['revision'])
        with self.assertRaisesRegex(ValueError,'이전 검토 버전'): self.approve(a)
        with self.assertRaisesRegex(ValueError,'사람 승인 없음'): self.r.apply('batch',['one'])
        self.r.apply('batch',['two'])

    def test_tampering_after_card_or_display_fails(self):
        result=self.prepare(); self.approve(result)
        folder=Path(result['review']).parent
        for path in [folder/'after/concepts/a.md.txt',folder/'before/concepts/a.md.txt',folder/'review.md',folder/'card.json']:
            old=path.read_bytes()
            if path.name=='card.json':
                card=json.loads(old); card['summary']='different'; path.write_text(json.dumps(card), encoding='utf-8')
            else: path.write_bytes(old+b'changed')
            with self.assertRaises(ValueError): self.r.apply('batch',['one'])
            path.write_bytes(old)

    def test_stale_target_and_basis_block_apply(self):
        result=self.prepare(); self.approve(result)
        for path in [self.raw,self.wiki/'concepts/a.md']:
            old=path.read_bytes(); path.write_bytes(old.replace(b'old',b'changed') if path!=self.raw else b'changed\n')
            with self.assertRaisesRegex(ValueError,'기준 변경'): self.r.apply('batch',['one'])
            path.write_bytes(old)
        self.r.apply('batch',['one'])

    def test_linked_context_is_a_dependency(self):
        self.put('concepts/context.md',page('context'))
        result=self.prepare(files={'concepts/a.md':page('a','[[context]]')}); self.approve(result)
        self.put('concepts/context.md',page('context','changed'))
        with self.assertRaisesRegex(ValueError,'기준 변경'): self.r.apply('batch',['one'])

    def test_shared_page_topics_rejected(self):
        self.prepare()
        with self.assertRaisesRegex(ValueError,'한 승인 묶음'): self.prepare('two')

    def test_partial_link_dependency_fails_and_combined_succeeds(self):
        a=self.prepare(files={'concepts/a.md':page('a','[[b]]')})
        b=self.prepare('two',{'concepts/b.md':page('b','[[a]]')})
        self.approve(a); self.approve(b)
        with self.assertRaisesRegex(ValueError,'없는 페이지'): self.r.apply('batch',['one'])
        self.r.apply('batch',['one','two'])

    def test_scope_checks_aliases_in_both_directions(self):
        self.put('concepts/other.md',page('other','[[wiki/concepts/a|alias]]'))
        result=self.prepare(link_constraints=[{'target':'concepts/a','inbound_from':[]}])
        self.approve(result)
        with self.assertRaisesRegex(ValueError,'승인 범위 밖 연결'): self.r.apply('batch',['one'])
        with self.assertRaisesRegex(ValueError,'승인 범위 밖 연결'):
            self.r.check_constraints([{'link_constraints':[{'target':'concepts/other','outbound_to':[]}]}],self.r.pages())

    def test_verification_history_must_survive(self):
        old=page('a').replace(b'verified: []',b'verified: [{by: human:owner, at: old-date}]')
        self.put('concepts/a.md',old)
        with self.assertRaisesRegex(ValueError,'사람 검증 이력'): self.prepare()
        good=page('a','new','verification_history: [{by: human:owner, at: old-date, revision: prior-sha, scope: prior-body}]\n')
        self.prepare(files={'concepts/a.md':good})
        self.put('concepts/a.md',good)
        with self.assertRaisesRegex(ValueError,'기존 검증 이력'): self.prepare()
        with self.assertRaisesRegex(ValueError,'verified는 비워'): self.prepare(files={'concepts/a.md':old})

    def test_paths_and_symlinks_rejected(self):
        with self.assertRaisesRegex(ValueError,'페이지 상대경로'): self.prepare(files={'../escape.md':page('bad')})
        (self.wiki/'concepts/a.md').unlink()
        try:
            (self.wiki/'concepts/a.md').symlink_to(self.raw)
        except OSError:
            self.skipTest('Directory permissions do not allow symlinks')
        with self.assertRaisesRegex(ValueError,'심링크'): self.prepare()

    def test_missing_citation_and_review_link_fail(self):
        with self.assertRaisesRegex(ValueError,'근거 범위 오류'): self.prepare(files={'concepts/a.md':page('a','^[/raw.md:999]')})
        self.prepare(files={'concepts/a.md':page('a','[[reviews/bad]]')})
        with self.assertRaisesRegex(ValueError,'없는 페이지'): self.r.preview('batch',['one'])

    def test_overlay_resources_use_proposed_version(self):
        self.prepare(files={'concepts/a.md':page('a','short')})
        self.put('concepts/c.md',page('c','^[/docs/wiki/concepts/a.md:50]'))
        # The real page has enough lines; the candidate does not.
        self.put('concepts/a.md',page('a','old\n'*60))
        self.prepare(files={'concepts/a.md':page('a','short')})
        with self.assertRaisesRegex(ValueError,'인용 줄 범위 오류'): self.r.preview('batch',['one'])

    def test_review_citations_are_not_authoritative(self):
        self.put('reviews/proposal.md', b'speculative claim\n')
        for body, extra in [
            ('^[/docs/wiki/reviews/proposal.md:1]', ''),
            ('new', 'sources: [{resource: /docs/wiki/reviews/proposal.md}]\n'),
        ]:
            self.prepare(files={'concepts/a.md':page('a',body,extra)})
            with self.assertRaisesRegex(ValueError,'검토 사본'): self.r.preview('batch',['one'])

    def test_clippings_drafts_do_not_count_as_processed(self):
        import clippings_todo
        self.put('reviews/working/source.md',page('draft','text','sources: [{resource: /Clippings/clip.md}]\n'))
        with patch.object(wikilib,'WIKI_ROOT',self.wiki):
            self.assertNotIn('clip.md',clippings_todo.processed())
            self.put('sources/clip.md',page('published','text','sources: [{resource: /Clippings/clip.md}]\n'))
            self.assertIn('clip.md',clippings_todo.processed())

    def test_joint_new_page_citation_uses_sealed_draft(self):
        result=self.prepare(files={
            'concepts/a.md':page('a','^[/docs/wiki/concepts/new.md:7]'),
            'concepts/new.md':page('new','[[a]]'),
        })
        self.approve(result)
        self.r.apply('batch',['one'])

    def test_misspelled_scope_constraint_fails_closed(self):
        self.prepare(link_constraints=[{'target':'concepts/a','inbound_form':[]}])
        with self.assertRaisesRegex(ValueError,'link_constraints'): self.r.preview('batch',['one'])

    def test_partial_write_failure_rolls_back(self):
        result=self.prepare(); self.approve(result)
        original=review.atomic
        failed=False
        def fail_once(path,data):
            nonlocal failed
            if path==self.wiki/'index.md' and not failed:
                failed=True
                raise OSError('simulated disk error')
            return original(path,data)
        with patch.object(review,'atomic',fail_once):
            with self.assertRaisesRegex(OSError,'simulated'): self.r.apply('batch',['one'])
        self.assertEqual((self.wiki/'concepts/a.md').read_bytes(),page('a','old'))
        self.assertFalse((self.wiki/'index.md').exists())
        self.assertFalse(self.r.journal.exists())
        self.r.apply('batch',['one'])

    def test_recovery_refuses_overwriting_unrelated_edit(self):
        self.r.root.mkdir()
        self.r.journal.write_text(json.dumps({'concepts/a.md':{'before':'old','after':'new'}}), encoding='utf-8')
        self.put('concepts/a.md',b'third party')
        with self.assertRaisesRegex(ValueError,'다른 변경'): self.r.recover()
        self.put('concepts/a.md',b'new')
        self.r.recover()
        self.assertEqual((self.wiki/'concepts/a.md').read_bytes(),b'old')


if __name__=='__main__': unittest.main()
