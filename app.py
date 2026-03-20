#需要先下载库 pip install streamlit openai
#运行：streamlit run ai_partner.py
import streamlit as st
import os
from openai import OpenAI
from datetime import datetime
import json

#创建与ai大模型交互的客户端对象,这里需要去deepseek开发平台获取apikey
client = OpenAI(
    api_key="sk-你的实际apikey",
    base_url="https://api.deepseek.com")  # API_KEY是Deepseek的API_KEY

#设置页面配置项
st.set_page_config(
    page_title="AI智能伴侣",
    page_icon='🥰',
    #布局
    layout="wide",
    #控制侧边栏
    initial_sidebar_state='expanded',
    menu_items={
        'About':"Welcome to Ai-Partner！"})


#加载所有对话列表信息
def load_sessions():
    sessions_list= []
    if os.path.exists("sessions"):
        file_list=os.listdir("sessions")
        for filename in file_list:
            if filename.endswith(".json"):
                sessions_list.append(filename[:-5])
    sessions_list.sort(reverse=True)  #时间降序排序
    return sessions_list

#生成会话标识
def generate_session_name():
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

#保存会话
def save_session():
    if st.session_state.current_session:
        #构建新会话对象
        st.session_data = {
            "nick_name": st.session_state.nickname,
            "nature": st.session_state.nature,
            "current_session": st.session_state.current_session,
            "messages": st.session_state.messages
        }

        # 如果sessions目录不存在，则创建
        if not os.path.exists("sessions"):
            os.mkdir("sessions")

        # 保存会话数据
        with open(f"sessions/{st.session_state.current_session}.json", "w", encoding="utf-8") as f:
            json.dump(st.session_data, f, ensure_ascii=False, indent=2)


#加载会话信息
def load_session(session_name):
    try:
        if os.path.exists(f"sessions/{session_name}.json"):
            with open(f"sessions/{session_name}.json", "r", encoding="utf-8") as f:
                st.session_data = json.load(f)
                st.session_state.nickname = st.session_data["nick_name"]
                st.session_state.nature = st.session_data["nature"]
                st.session_state.current_session = st.session_data["current_session"]
                st.session_state.messages = st.session_data["messages"]
    except Exception:
        st.error("会话加载失败")


#删除会话
def delete_session(session_name):
    try:
        if os.path.exists(f"sessions/{session_name}.json"):
            os.remove(f"sessions/{session_name}.json")
            #如果删除当前会话，需更新消息列表
            if session_name == st.session_state.current_session:
                st.session_state.messages = []
                st.session_state.current_session = generate_session_name()
    except Exception:
        st.error("会话删除失败")



#大标题
st.title("AI智能伴侣")

system_prompt = '''你是%s，回复按以下规则
1.用挑逗的语气回复问题，但是都会回答正确问题
2.在上闽江大学，福建人，聊天带台湾腔调
3.用符合伴侣性格的方式对话
4.有需要时可以用emoji表情
- %s
'''


#初始化聊天信息
if 'messages' not in st.session_state:
    st.session_state.messages = []
#昵称
if 'nickname' not in st.session_state:
    st.session_state.nickname = '小徐'
if 'nature' not in st.session_state:
    st.session_state.nature = ' 专业技术人员，按正确答案回答'
if "current_session" not in st.session_state:
    st.session_state.current_session=generate_session_name()


#展示聊天信息
st.text(f"会话名称：{st.session_state.current_session}")
for message in st.session_state.messages:
    if message["role"] == "user":
        st.markdown(
            f'👑 朕：{message["content"]}',
        )
    else:
        st.markdown(
            f'💖 {st.session_state.nickname}：{message["content"]}',
        )


#左侧侧边栏 - with:streamlit中上下文管理器
with st.sidebar:
    st.subheader("AI控制面板")

    if st.button("🖋️新建会话",use_container_width=True):
        #保存会话
        save_session()
        #新建会话
        if st.session_state.messages: # 如果聊天信息非空，True；否则为False
            st.session_state.messages = []
            st.session_state.current_session = generate_session_name()
            save_session()
            st.rerun()  # 重新运行当前页面

    #会话历史
    st.text("会话历史")
    session_list=load_sessions()
    for session in session_list:
        col1,col2=st.columns([4,1])
        with col1:
            #加载会话信息
            if st.button(session,use_container_width=True,key=f"load_{session}",type="primary" if session==st.session_state.current_session else "secondary"):
                load_session(session)
                st.rerun()
        with col2:
            #删除会话信息
            if st.button("❌",use_container_width=True, key=f"delete_{session}"):
                delete_session(session)
                st.rerun()

    #分割线
    st.divider()

    st.subheader("伴侣信息")
    nickname = st.text_input("昵称",placeholder="请输入昵称",value=st.session_state.nickname)
    if nickname:
        st.session_state.nickname = nickname

    nature=st.text_input("性格",placeholder="请输入性格",value=st.session_state.nature)
    if nature:
        st.session_state.nature = nature



#消息输入框
with st.form(key="chat_form", clear_on_submit=True):
    prompt = st.text_input("请输入您要问的问题：")
    submit = st.form_submit_button("发送")
if submit and prompt:
    st.markdown(
        f'<div class="user-bubble">👑 朕：{prompt}</div>',
        unsafe_allow_html=True
    )
    print("----------->调用AI大模型，提示词：", prompt)
    #保存用户输入的提示词
    st.session_state.messages.append({"role": "user", "content": prompt})


    # 调用大模型
    response = client.chat.completions.create(
        model="deepseek-chat",  #换成 deepseek-reasoner 则对应 DeepSeek-V3.2 的思考模式
        messages=[
            {"role": "system", "content": system_prompt % (st.session_state.nickname,st.session_state.nature)},
            *st.session_state.messages,
        ],
        stream=True
    )


    #流式输出
    response_message=st.empty()
    full_response = ""
    #  流式更新：只修改这个容器，不会新增行
    for chunk in response:
        if chunk.choices[0].delta.content:
            full_response += chunk.choices[0].delta.content
            response_message.markdown(
                f'<div class="assistant-bubble">💖 {st.session_state.nickname}：{full_response}</div>',
                unsafe_allow_html=True
            )
    # 流式结束后，把完整消息存入会话，容器会自动被历史渲染覆盖
    st.session_state.messages.append({"role": "assistant", "content": full_response})


#非流式输出
    # print('<-------------大模型返回结果：',response.choices[0].message.content)
    # st.write(f"{st.session_state.nickname}：{response.choices[0].message.content}")
    #保存大模型返回结果
    # st.session_state.messages.append({"role": "assistant", "content": response.choices[0].message.content})

    save_session()
