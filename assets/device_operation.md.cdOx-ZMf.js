import{_ as a,o as s,c as e,R as n}from"./chunks/framework.OPRPu5cH.js";const q=JSON.parse('{"title":"","description":"","frontmatter":{},"headers":[],"relativePath":"device_operation.md","filePath":"device_operation.md","lastUpdated":1708172063000}'),t={name:"device_operation.md"},o=n(`<h2 id="使用方法" tabindex="-1">使用方法： <a class="header-anchor" href="#使用方法" aria-label="Permalink to &quot;使用方法：&quot;">​</a></h2><div class="language- vp-adaptive-theme"><button title="Copy Code" class="copy"></button><span class="lang"></span><pre class="shiki github-dark vp-code-dark"><code><span class="line"><span style="color:#e1e4e8;">import device_operation</span></span>
<span class="line"><span style="color:#e1e4e8;"></span></span>
<span class="line"><span style="color:#e1e4e8;">device_operation.api(operation,simulator_type,multi_instance) #注：部分参数注释会表明用哪几个参数</span></span></code></pre><pre class="shiki github-light vp-code-light"><code><span class="line"><span style="color:#24292e;">import device_operation</span></span>
<span class="line"><span style="color:#24292e;"></span></span>
<span class="line"><span style="color:#24292e;">device_operation.api(operation,simulator_type,multi_instance) #注：部分参数注释会表明用哪几个参数</span></span></code></pre></div><h2 id="操作类型" tabindex="-1">操作类型： <a class="header-anchor" href="#操作类型" aria-label="Permalink to &quot;操作类型：&quot;">​</a></h2><p>请查阅simulator_api.py源代码，命名非常易读，包含注释 由于可能会实时更新，故不一定在此处能完整贴出全部操作类型</p><div class="language- vp-adaptive-theme"><button title="Copy Code" class="copy"></button><span class="lang"></span><pre class="shiki github-dark vp-code-dark"><code><span class="line"><span style="color:#e1e4e8;">&quot;get_adb_address&quot;</span></span>
<span class="line"><span style="color:#e1e4e8;">&quot;get_running_simulators&quot;</span></span>
<span class="line"><span style="color:#e1e4e8;">&quot;get_adb_address_by_uuid&quot;</span></span>
<span class="line"><span style="color:#e1e4e8;">&quot;get_simulator_uuid&quot;</span></span>
<span class="line"><span style="color:#e1e4e8;">&quot;terminate_simulator_name&quot;</span></span>
<span class="line"><span style="color:#e1e4e8;">&quot;terminate_simulator_pid&quot;</span></span>
<span class="line"><span style="color:#e1e4e8;">&quot;get_simulator_commandline_name&quot;</span></span>
<span class="line"><span style="color:#e1e4e8;">&quot;get_simulator_commandline_pid&quot;</span></span>
<span class="line"><span style="color:#e1e4e8;">&quot;get_simulator_commandline_uuid&quot;</span></span></code></pre><pre class="shiki github-light vp-code-light"><code><span class="line"><span style="color:#24292e;">&quot;get_adb_address&quot;</span></span>
<span class="line"><span style="color:#24292e;">&quot;get_running_simulators&quot;</span></span>
<span class="line"><span style="color:#24292e;">&quot;get_adb_address_by_uuid&quot;</span></span>
<span class="line"><span style="color:#24292e;">&quot;get_simulator_uuid&quot;</span></span>
<span class="line"><span style="color:#24292e;">&quot;terminate_simulator_name&quot;</span></span>
<span class="line"><span style="color:#24292e;">&quot;terminate_simulator_pid&quot;</span></span>
<span class="line"><span style="color:#24292e;">&quot;get_simulator_commandline_name&quot;</span></span>
<span class="line"><span style="color:#24292e;">&quot;get_simulator_commandline_pid&quot;</span></span>
<span class="line"><span style="color:#24292e;">&quot;get_simulator_commandline_uuid&quot;</span></span></code></pre></div><h2 id="支持的操作" tabindex="-1">支持的操作 <a class="header-anchor" href="#支持的操作" aria-label="Permalink to &quot;支持的操作&quot;">​</a></h2><p>结束进程 启动进程 获取模拟器adb端口 获取模拟器命令行参数 为模拟器生成唯一uuid</p>`,7),l=[o];function p(i,c,r,u,d,_){return s(),e("div",null,l)}const h=a(t,[["render",p]]);export{q as __pageData,h as default};
