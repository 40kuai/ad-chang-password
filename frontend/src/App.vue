<script setup>
import { reactive, ref, computed } from "vue";

const form = reactive({
  username: "",
  oldPassword: "",
  newPassword: "",
  confirmPassword: ""
});

const showPwd = reactive({
  old: false,
  new: false,
  confirm: false
});

const loading = ref(false);
const result = ref(null); // { success, message }
const touched = reactive({ username: false, oldPassword: false, newPassword: false, confirmPassword: false });

const PWD_RULES = {
  min: 8,
  max: 64,
  pattern: /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z0-9]).+$/
};

const fieldErrors = computed(() => {
  const e = {};
  if (touched.username && !form.username.trim()) e.username = "请输入域账号";
  if (touched.oldPassword && !form.oldPassword) e.oldPassword = "请输入旧密码";
  if (touched.newPassword) {
    if (!form.newPassword) e.newPassword = "请输入新密码";
    else if (form.newPassword.length < PWD_RULES.min) e.newPassword = `密码长度至少 ${PWD_RULES.min} 位`;
    else if (form.newPassword.length > PWD_RULES.max) e.newPassword = `密码长度不能超过 ${PWD_RULES.max} 位`;
    else if (!PWD_RULES.pattern.test(form.newPassword)) e.newPassword = "需包含大小写字母、数字和特殊字符";
    else if (form.newPassword === form.oldPassword) e.newPassword = "新密码不能与旧密码相同";
  }
  if (touched.confirmPassword && form.confirmPassword !== form.newPassword) e.confirmPassword = "两次输入的新密码不一致";
  return e;
});

const canSubmit = computed(() => {
  return (
    form.username.trim() &&
    form.oldPassword &&
    form.newPassword &&
    form.confirmPassword &&
    Object.keys(fieldErrors.value).length === 0
  );
});

function blurField(name) {
  touched[name] = true;
}

function toggleShow(key) {
  showPwd[key] = !showPwd[key];
}

async function onSubmit() {
  result.value = null;
  loading.value = true;
  try {
    const resp = await fetch("/api/change-password", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        username: form.username.trim(),
        old_password: form.oldPassword,
        new_password: form.newPassword
      })
    });
    const data = await resp.json();
    result.value = { success: data.code === 0, message: data.message || "操作失败，请稍后重试" };
    if (data.code === 0) {
      form.username = "";
      form.oldPassword = "";
      form.newPassword = "";
      form.confirmPassword = "";
      Object.keys(touched).forEach((k) => (touched[k] = false));
    }
  } catch (err) {
    result.value = { success: false, message: "网络异常，请检查网络或稍后重试" };
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <div class="page">
    <div class="card">
      <header class="header">
        <div class="logo">🔐</div>
        <h1>AD 域控自助改密平台</h1>
        <p class="sub">请输入域账号与密码信息，修改您的 Windows 域登录密码</p>
      </header>

      <form class="form" @submit.prevent="onSubmit" novalidate>
        <div class="field">
          <label for="username">域账号</label>
          <input
            id="username"
            v-model="form.username"
            type="text"
            autocomplete="username"
            placeholder="例如 zhangsan"
            @blur="blurField('username')"
          />
          <p v-if="fieldErrors.username" class="err">{{ fieldErrors.username }}</p>
        </div>

        <div class="field">
          <label for="oldPassword">旧密码</label>
          <div class="pwd-wrap">
            <input
              id="oldPassword"
              v-model="form.oldPassword"
              :type="showPwd.old ? 'text' : 'password'"
              autocomplete="current-password"
              placeholder="请输入当前使用的密码"
              @blur="blurField('oldPassword')"
            />
            <button type="button" class="eye" @click="toggleShow('old')">{{ showPwd.old ? '隐藏' : '显示' }}</button>
          </div>
          <p v-if="fieldErrors.oldPassword" class="err">{{ fieldErrors.oldPassword }}</p>
        </div>

        <div class="field">
          <label for="newPassword">新密码</label>
          <div class="pwd-wrap">
            <input
              id="newPassword"
              v-model="form.newPassword"
              :type="showPwd.new ? 'text' : 'password'"
              autocomplete="new-password"
              placeholder="至少 8 位，含大小写字母、数字和特殊字符"
              @blur="blurField('newPassword')"
            />
            <button type="button" class="eye" @click="toggleShow('new')">{{ showPwd.new ? '隐藏' : '显示' }}</button>
          </div>
          <p v-if="fieldErrors.newPassword" class="err">{{ fieldErrors.newPassword }}</p>
        </div>

        <div class="field">
          <label for="confirmPassword">确认新密码</label>
          <div class="pwd-wrap">
            <input
              id="confirmPassword"
              v-model="form.confirmPassword"
              :type="showPwd.confirm ? 'text' : 'password'"
              autocomplete="new-password"
              placeholder="再次输入新密码"
              @blur="blurField('confirmPassword')"
            />
            <button type="button" class="eye" @click="toggleShow('confirm')">{{ showPwd.confirm ? '隐藏' : '显示' }}</button>
          </div>
          <p v-if="fieldErrors.confirmPassword" class="err">{{ fieldErrors.confirmPassword }}</p>
        </div>

        <div v-if="result" class="result" :class="result.success ? 'ok' : 'fail'">
          {{ result.message }}
        </div>

        <button class="submit" type="submit" :disabled="!canSubmit || loading">
          {{ loading ? '提交中…' : '修改密码' }}
        </button>
      </form>

      <footer class="footer">修改成功后，请使用新密码重新登录企业系统。</footer>
    </div>
  </div>
</template>

<style>
* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}
body {
  font-family: "PingFang SC", "Microsoft YaHei", -apple-system, sans-serif;
  background: linear-gradient(135deg, #1e3a5f 0%, #2d5f8a 100%);
  min-height: 100vh;
}
.page {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  padding: 20px;
}
.card {
  width: 100%;
  max-width: 420px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.25);
  padding: 32px 28px;
}
.header {
  text-align: center;
  margin-bottom: 24px;
}
.logo {
  font-size: 36px;
  margin-bottom: 8px;
}
.header h1 {
  font-size: 20px;
  color: #1e3a5f;
}
.sub {
  margin-top: 6px;
  font-size: 13px;
  color: #8a94a6;
}
.form .field {
  margin-bottom: 16px;
}
.form label {
  display: block;
  font-size: 13px;
  color: #4a5568;
  margin-bottom: 6px;
  font-weight: 500;
}
.form input {
  width: 100%;
  height: 42px;
  padding: 0 12px;
  border: 1px solid #d6dce5;
  border-radius: 8px;
  font-size: 14px;
  outline: none;
  transition: border-color 0.2s;
}
.form input:focus {
  border-color: #2d5f8a;
}
.pwd-wrap {
  position: relative;
}
.pwd-wrap input {
  padding-right: 52px;
}
.eye {
  position: absolute;
  right: 8px;
  top: 50%;
  transform: translateY(-50%);
  border: none;
  background: none;
  color: #2d5f8a;
  font-size: 12px;
  cursor: pointer;
  padding: 4px;
}
.err {
  margin-top: 4px;
  font-size: 12px;
  color: #e53e3e;
}
.result {
  padding: 10px 12px;
  border-radius: 8px;
  font-size: 13px;
  margin-bottom: 16px;
}
.result.ok {
  background: #f0fff4;
  color: #276749;
  border: 1px solid #c6f6d5;
}
.result.fail {
  background: #fff5f5;
  color: #c53030;
  border: 1px solid #fed7d7;
}
.submit {
  width: 100%;
  height: 44px;
  border: none;
  border-radius: 8px;
  background: #2d5f8a;
  color: #fff;
  font-size: 15px;
  cursor: pointer;
  transition: background 0.2s, opacity 0.2s;
}
.submit:hover:not(:disabled) {
  background: #1e4a6e;
}
.submit:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.footer {
  margin-top: 20px;
  text-align: center;
  font-size: 12px;
  color: #a0aec0;
}
</style>
