import{_ as s,c as a,a2 as e,o as p}from"./chunks/framework.By2iWbs8.js";const u=JSON.parse('{"title":"开发过程中的约定","description":"","frontmatter":{},"headers":[],"relativePath":"develop_doc/develop_format.md","filePath":"develop_doc/develop_format.md","lastUpdated":1743918177000}'),l={name:"develop_doc/develop_format.md"};function i(o,n,t,c,r,d){return p(),a("div",null,n[0]||(n[0]=[e(`<h1 id="开发过程中的约定" tabindex="-1">开发过程中的约定 <a class="header-anchor" href="#开发过程中的约定" aria-label="Permalink to &quot;开发过程中的约定&quot;">​</a></h1><h2 id="关于-gitignore" tabindex="-1">关于 <code>.gitignore</code> <a class="header-anchor" href="#关于-gitignore" aria-label="Permalink to &quot;关于 \`.gitignore\`&quot;">​</a></h2><ul><li><strong>不在项目根目录下设置 <code>.gitignore</code> 文件。</strong></li><li>每位开发者应设置自己的 <code>.git/info/exclude</code> 文件，用于忽略与其开发环境相关的文件。</li></ul><h3 id="原因" tabindex="-1">原因 <a class="header-anchor" href="#原因" aria-label="Permalink to &quot;原因&quot;">​</a></h3><ul><li><strong>根目录下的 <code>.gitignore</code> 文件：</strong><br> 会影响到其他开发者的工作环境。</li><li><strong><code>.git/info/exclude</code> 文件：</strong><br> 仅在当前开发者的本地环境生效，确保每位开发者的忽略设置独立、互不干扰。</li></ul><p><strong>你可以参考下面的<code>.gitignore</code></strong></p><div class="language-.gitignore vp-adaptive-theme"><button title="Copy Code" class="copy"></button><span class="lang">.gitignore</span><pre class="shiki shiki-themes github-light github-dark vp-code" tabindex="0"><code><span class="line"><span>/*</span></span>
<span class="line"><span></span></span>
<span class="line"><span>!cli.example.py</span></span>
<span class="line"><span>!service.example.py</span></span>
<span class="line"><span>!src</span></span>
<span class="line"><span>!module</span></span>
<span class="line"><span>!gui</span></span>
<span class="line"><span>!docs</span></span>
<span class="line"><span>!core</span></span>
<span class="line"><span>!deploy</span></span>
<span class="line"><span>!device_operation</span></span>
<span class="line"><span>!develop_tools</span></span>
<span class="line"><span></span></span>
<span class="line"><span>!.editorconfig</span></span>
<span class="line"><span>!.gitignore</span></span>
<span class="line"><span>!LICENSE</span></span>
<span class="line"><span>!README.md</span></span>
<span class="line"><span></span></span>
<span class="line"><span>!main.py</span></span>
<span class="line"><span>!requirements.txt</span></span>
<span class="line"><span>!window.py</span></span>
<span class="line"><span>!requirements-i18n.txt</span></span>
<span class="line"><span>!requirements-linux.txt</span></span>
<span class="line"><span>*.pyc</span></span>
<span class="line"><span>*.xml</span></span></code></pre></div>`,7)]))}const m=s(l,[["render",i]]);export{u as __pageData,m as default};
