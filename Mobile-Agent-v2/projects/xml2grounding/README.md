# Grounding Task Pretrain

```shell
    # 通过 XML 解析框选数据 
    python Mobile-Agent-v2/projects/xml2grounding/Step1_Parse_XML.py demo.json --trajectory-xml-folder 'D:\workspace\feikuai'
    python Mobile-Agent-v2/projects/xml2grounding/Step1_Parse_XML.py demo.json --trajectory-xml-folder 'D:\workspace\feikuai\2024-10-23_09-50-17'
    python Mobile-Agent-v2/projects/xml2grounding/Step1_Parse_XML.py demo.json --trajectory-xml-folder 'D:\workspace\feikuai\2024-10-23_09-50-17' --check-xml-list
    python Mobile-Agent-v2/projects/xml2grounding/Step1_Parse_XML.py demo.json --trajectory-xml-folder 'D:\workspace\feikuai\2024-10-23_10-27-11' --check-xml-list
    python Mobile-Agent-v2/projects/xml2grounding/Step1_Parse_XML.py demo.json --trajectory-xml-folder 'D:\workspace\feikuai\2024-10-23_20-17-28'

    # 生成 对话数据模板用于 VLM 进行SFT
    # 多张手机截图的 批量标注数据导出 作为输入，通过该脚本得到 微调数据 格式作为训练输入
    python Mobile-Agent-v2/projects/xml2grounding/Step2_RE_generate.py


    # 必须内网
    python Mobile-Agent-v2/projects/xml2grounding/mify_model.py

    # camel
    python examples/vision/image_crafting.py
    python examples/vision/object_recognition.py --image_paths 'D:\workspace\feikuai\2024-10-23_09-50-17\screenshot_1729648219.png'
```