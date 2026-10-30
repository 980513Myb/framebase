import asyncio
import json
import os
import tempfile
import unittest
import zipfile
from io import BytesIO
from unittest.mock import patch

from fastapi import HTTPException, UploadFile

from app.routers import resources


def template_bytes(name="自由模板"):
    return json.dumps({"name": name, "engine": "自由设计", "config": {"designer_elements": []}}, ensure_ascii=False).encode("utf-8")


async def response_bytes(response):
    chunks = []
    async for chunk in response.body_iterator:
        chunks.append(chunk)
    return b"".join(chunks)


class TemplateExchangeTests(unittest.TestCase):
    @staticmethod
    def write_template(directory, filename, name, engine):
        with open(os.path.join(directory, filename), "w", encoding="utf-8") as template_file:
            json.dump({"name": name, "engine": engine, "config": {}}, template_file, ensure_ascii=False)

    def test_json_import_keeps_existing_template(self):
        with tempfile.TemporaryDirectory() as tempdir, patch.object(resources, "TEMPLATES_DIR", tempdir):
            first = UploadFile(filename="designer.json", file=BytesIO(template_bytes()))
            second = UploadFile(filename="designer.json", file=BytesIO(template_bytes("第二份")))
            first_result = asyncio.run(resources.upload_template(first))
            second_result = asyncio.run(resources.upload_template(second))

            self.assertEqual(first_result["filenames"], ["designer.json"])
            self.assertEqual(second_result["filenames"], ["designer_1.json"])
            self.assertTrue(os.path.isfile(os.path.join(tempdir, "designer.json")))
            self.assertTrue(os.path.isfile(os.path.join(tempdir, "designer_1.json")))

    def test_batch_export_contains_json_and_preview(self):
        with tempfile.TemporaryDirectory() as tempdir, patch.object(resources, "TEMPLATES_DIR", tempdir):
            with open(os.path.join(tempdir, "designer.json"), "wb") as template_file:
                template_file.write(template_bytes())
            with open(os.path.join(tempdir, "designer.jpg"), "wb") as preview_file:
                preview_file.write(b"preview")

            response = resources.export_templates({"filenames": ["designer.json"]})
            archive_data = asyncio.run(response_bytes(response))
            with zipfile.ZipFile(BytesIO(archive_data)) as archive:
                self.assertEqual(set(archive.namelist()), {"designer.json", "designer.jpg"})

    def test_template_manager_groups_each_user_template_after_system_groups(self):
        with tempfile.TemporaryDirectory() as templates_dir, tempfile.TemporaryDirectory() as defaults_dir, tempfile.TemporaryDirectory() as layouts_dir:
            self.write_template(defaults_dir, "builtin.json", "系统默认", "经典平铺")
            self.write_template(templates_dir, "builtin.json", "系统默认", "经典平铺")
            self.write_template(templates_dir, "designer_a.json", "测试", "自由设计")
            self.write_template(templates_dir, "designer_b.json", "第二套默认模板", "自由设计")
            open(os.path.join(layouts_dir, "经典平铺.py"), "w", encoding="utf-8").close()
            open(os.path.join(layouts_dir, "自由设计.py"), "w", encoding="utf-8").close()
            os.utime(os.path.join(templates_dir, "designer_a.json"), (100, 100))
            os.utime(os.path.join(templates_dir, "designer_b.json"), (200, 200))

            with patch.object(resources, "TEMPLATES_DIR", templates_dir), patch.object(resources, "DEFAULT_TEMPLATES_DIR", defaults_dir), patch.object(resources, "LAYOUTS_DIR", layouts_dir):
                result = resources.get_templates_v2()

        self.assertEqual([group["kind"] for group in result["data"]], ["system", "user", "user"])
        self.assertEqual([group["title"] for group in result["data"]], ["经典平铺模式", "测试", "第二套默认模板"])
        self.assertEqual([len(group["presets"]) for group in result["data"]], [1, 1, 1])
        self.assertTrue(result["data"][0]["presets"][0]["is_builtin"])
        self.assertTrue(all(group["presets"][0]["can_delete"] for group in result["data"][1:]))

    def test_builtin_template_cannot_be_deleted_but_user_template_can(self):
        with tempfile.TemporaryDirectory() as templates_dir, tempfile.TemporaryDirectory() as defaults_dir:
            self.write_template(defaults_dir, "builtin.json", "系统默认", "经典平铺")
            self.write_template(templates_dir, "builtin.json", "系统默认", "经典平铺")
            self.write_template(templates_dir, "designer.json", "测试", "自由设计")
            with open(os.path.join(templates_dir, "designer.jpg"), "wb") as preview_file:
                preview_file.write(b"preview")

            with patch.object(resources, "TEMPLATES_DIR", templates_dir), patch.object(resources, "DEFAULT_TEMPLATES_DIR", defaults_dir):
                with self.assertRaises(HTTPException) as blocked:
                    resources.delete_template({"filename": "builtin.json"})
                deleted = resources.delete_template({"filename": "designer.json"})

            self.assertEqual(blocked.exception.status_code, 403)
            self.assertTrue(os.path.isfile(os.path.join(templates_dir, "builtin.json")))
            self.assertEqual(deleted, {"status": "ok"})
            self.assertFalse(os.path.exists(os.path.join(templates_dir, "designer.json")))
            self.assertFalse(os.path.exists(os.path.join(templates_dir, "designer.jpg")))


if __name__ == "__main__":
    unittest.main()
