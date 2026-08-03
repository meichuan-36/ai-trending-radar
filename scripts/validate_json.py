import json, sys, os

def validate(file_path, required_fields=["name", "url", "stars", "description", "language", "topics"]):
    if not os.path.exists(file_path):
        print(f"⚠️ 文件不存在：{file_path}")
        sys.exit(1)
    with open(file_path, "r") as f:
        data = json.load(f)
    if not isinstance(data, list):
        print(f"❌ {file_path} 不是数组")
        sys.exit(1)
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

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("用法: python validate_json.py <文件路径>")
        sys.exit(1)
    validate(sys.argv[1])
