import json, sys, os


def validate(file_path, required_fields=["name", "url", "stars", "description", "language", "topics"]):
    if not os.path.exists(file_path):
        print(f"⚠️ 文件不存在：{file_path}")
        sys.exit(1)
    with open(file_path, "r") as f:
        data = json.load(f)

    # If the file is a list of items (e.g., semiannual.json)
    if isinstance(data, list):
        for i, item in enumerate(data):
            if not isinstance(item, dict):
                print(f"❌ 第 {i} 项不是对象")
                sys.exit(1)
            for field in required_fields:
                if field not in item:
                    print(f"❌ 第 {i} 项缺少字段 {field}")
                    sys.exit(1)
        print(f"✅ {file_path} 校验通过，包含 {len(data)} 个项目")
        sys.exit(0)

    # If the file is a dictionary (e.g., summary.json), validate expected summary fields
    if isinstance(data, dict):
        # Common expected keys for summary.json
        expected_summary_keys = ["total_repos", "avg_stars", "top_topics", "languages"]
        if all(k in data for k in expected_summary_keys):
            # Basic type checks
            if not isinstance(data.get("total_repos"), int):
                print(f"❌ {file_path} 字段 total_repos 类型错误，预期 int")
                sys.exit(1)
            if not (isinstance(data.get("avg_stars"), int) or isinstance(data.get("avg_stars"), float)):
                print(f"❌ {file_path} 字段 avg_stars 类型错误，预期数字")
                sys.exit(1)
            if not isinstance(data.get("top_topics"), list):
                print(f"❌ {file_path} 字段 top_topics 类型错误，预期数组")
                sys.exit(1)
            if not isinstance(data.get("languages"), dict):
                print(f"❌ {file_path} 字段 languages 类型错误，预期对象/字典")
                sys.exit(1)

            print(f"✅ {file_path} 校验通过 (summary)")
            sys.exit(0)
        else:
            # If it's a dict but not the expected summary structure, report it
            missing = [k for k in expected_summary_keys if k not in data]
            print(f"❌ {file_path} 是对象但缺少 summary 所需字段: {', '.join(missing)}")
            sys.exit(1)

    # Anything else is invalid for our validation
    print(f"❌ {file_path} 格式不符合预期（既不是数组也不是 summary 对象）")
    sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("用法: python validate_json.py <文件路径>")
        sys.exit(1)
    validate(sys.argv[1])
