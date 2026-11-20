import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch

ROOT = Path(__file__).parent
if not (ROOT / "scripts").is_dir():
    ROOT = ROOT.parent


class CredentialRouting(unittest.TestCase):
    def test_python_selects_admin_only_for_admin_paths(self):
        spec = importlib.util.spec_from_file_location("allocator_candidate", ROOT / "scripts/request_z_code.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        seen = []
        def reply(request, timeout):
            seen.append(request.get_header("Authorization"))
            return io.BytesIO(b'{"ok":true}')
        with patch.dict(os.environ, {"ZCODE_ADMIN_API_KEY": "admin-test"}), patch.object(module.urllib.request, "urlopen", reply):
            module.request("GET", "https://example.test/prefix/v1/admin/queue", "ordinary-test")
            module.request("GET", "https://example.test/v1/lookup?name_key=/v1/admin/queue", "ordinary-test")
            module.request("GET", "https://example.test/v1/administrator", "ordinary-test")
        with patch.dict(os.environ, {"ZCODE_ADMIN_API_KEY": ""}), patch.object(module.urllib.request, "urlopen", reply):
            module.request("GET", "https://example.test/v1/admin/queue", "legacy-test")
        self.assertEqual(seen, ["Bearer admin-test", "Bearer ordinary-test", "Bearer ordinary-test", "Bearer legacy-test"])

    def test_node_selects_admin_only_for_admin_paths(self):
        program = r'''
const fs = require('node:fs'); const vm = require('node:vm');
const source = fs.readFileSync(process.argv[1], 'utf8').split('\nmain().catch')[0];
const seen=[]; const env={ZCODE_ADMIN_API_KEY:'admin-test'};
const ctx={process:{env},URL,AbortSignal,setTimeout,console,
fetch:async (url,options)=>{seen.push(options.headers.Authorization);return {ok:true,status:200,text:async()=>'{"ok":true}'};}};
vm.createContext(ctx);vm.runInContext(source,ctx);
(async()=>{
await ctx.apiRequest('GET','https://example.test/prefix/v1/admin/queue','ordinary-test');
await ctx.apiRequest('GET','https://example.test/v1/lookup?name_key=/v1/admin/queue','ordinary-test');
await ctx.apiRequest('GET','https://example.test/v1/administrator','ordinary-test');
env.ZCODE_ADMIN_API_KEY='';
await ctx.apiRequest('GET','https://example.test/v1/admin/queue','legacy-test');
console.log(JSON.stringify(seen));})();
'''
        result = subprocess.run(["node", "-e", program, str(ROOT / "scripts/request_z_code.mjs")], capture_output=True, text=True, check=True)
        self.assertEqual(json.loads(result.stdout), ["Bearer admin-test", "Bearer ordinary-test", "Bearer ordinary-test", "Bearer legacy-test"])


if __name__ == "__main__":
    unittest.main()

