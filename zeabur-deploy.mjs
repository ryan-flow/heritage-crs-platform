import {
  createZeaburContext, listProjects, listServices,
  createProject, createService, deployFromSpecification,
  getRepoId, createEnvironmentVariable, waitForServicesRunning,
  getService
} from '@zeabur/ai-sdk';

const TOKEN = 'sk-milljfshg4ihquelh7emirt77gyqb';
const SERVER_ID = '6a06ef406525bc96a5a76b70';

const ctx = createZeaburContext(TOKEN);

// Runtime env vars from backend/.env
const ENV_VARS = {
  APP_NAME: 'China Intangible Cultural Heritage Platform API',
  APP_ENV: 'production',
  APP_DEBUG: 'false',
  API_PREFIX: '/api/v1',
  SQLITE_DB_FILE: 'data/heritage_platform.db',
  ADMIN_USERNAME: 'admin',
  ADMIN_PASSWORD: 'admin123',
  ADMIN_TOKEN: 'REPLACED_ADMIN_TOKEN',
  DOUBAO_API_URL: 'https://ark.cn-beijing.volces.com/api/v3/chat/completions',
  DOUBAO_API_KEY: 'REPLACED_API_KEY',
  DOUBAO_MODEL: 'doubao-seed-2-0-pro-260215',
  DOUBAO_TTS_APPID: 'REPLACED_TTS_APPID',
  DOUBAO_TTS_ACCESS_TOKEN: 'REPLACED_TTS_TOKEN',
  AI_SYSTEM_PROMPT: '你是中国非遗数字人导览官"非遗灵犀"，服务整个中国非物质文化遗产数字平台，不属于任何单一乡镇、景区或地方展馆。只回答与中国非物质文化遗产、代表性非遗项目、传统技艺、戏曲艺术、民俗活动、非遗保护政策、传承实践和非遗体验相关的问题；若问题超出范围，礼貌拒答并引导用户继续提问中国非遗相关内容。回答使用自然、优雅、口语化中文，保持单段或连续短段落，不要使用编号、项目符号、Markdown标题、来源说明或模型免责声明。避免地方导览身份表达。',
};

// Dockerfile for Python FastAPI backend (repo root context, backend in subdir)
const DOCKERFILE = [
  'FROM python:3.11-slim',
  'WORKDIR /app',
  'COPY backend/requirements.txt .',
  'RUN pip install --no-cache-dir -r requirements.txt',
  'COPY backend/ .',
  'RUN mkdir -p /app/data',
  'ENV PYTHONPATH=/app',
  'EXPOSE 8000',
  'CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]',
].join('\n');

async function main() {
  const regionCode = `server-${SERVER_ID}`;
  console.log(`Server: ${regionCode}`);

  // 1. Find GitHub repo
  console.log('\n=== 1. GitHub Repo ===');
  let repoId;
  for (const url of [
    'https://github.com/oldking-yes/heritage-crs-platform',
    'https://github.com/kukik-s/heritage-crs-platform',
  ]) {
    try {
      const result = JSON.parse(await getRepoId({ url }, ctx));
      repoId = result.getRepoId.id;
      console.log(`Found: ${result.getRepoId.full_name} (ID: ${repoId})`);
      break;
    } catch (e) {
      console.warn(`  ${url} → ${e.message}`);
    }
  }
  if (!repoId) throw new Error('Could not find GitHub repo');

  // 2. Find or create project (NEW project, not reuse existing)
  console.log('\n=== 2. Project ===');
  const PROJECT_NAME = 'heritage-crs-api';
  const { projects } = JSON.parse(await listProjects({}, ctx));
  let project = projects.edges.find(e => e.node.name === PROJECT_NAME);
  let projectId, envId;

  if (project) {
    projectId = project.node._id;
    envId = project.node.environments[0]._id;
    console.log(`Using existing project: ${projectId}`);
  } else {
    const result = JSON.parse(await createProject({ name: PROJECT_NAME, region: regionCode }, ctx));
    projectId = result.createProject._id;
    const { projects: p2 } = JSON.parse(await listProjects({}, ctx));
    const found = p2.edges.find(e => e.node._id === projectId);
    if (!found) throw new Error('Failed to find created project');
    envId = found.node.environments[0]._id;
    console.log(`Created project: ${projectId}, env: ${envId}`);
  }

  // 3. Find or create service
  console.log('\n=== 3. Service ===');
  const SERVICE_NAME = 'api';
  const svcData = JSON.parse(await listServices({ projectId }, ctx));
  let svc = svcData.services.edges.find(e => e.node.name === SERVICE_NAME);
  let serviceId;

  if (svc) {
    serviceId = svc.node._id;
    console.log(`Using existing service: ${serviceId} (${svc.node.status})`);
  } else {
    const result = JSON.parse(await createService({ name: SERVICE_NAME, projectId }, ctx));
    serviceId = result.createService._id;
    console.log(`Created service: ${serviceId}`);
  }

  // 4. Set environment variables
  console.log('\n=== 4. Environment Variables ===');
  for (const [key, value] of Object.entries(ENV_VARS)) {
    try {
      await createEnvironmentVariable({ serviceId, environmentId: envId, key, value }, ctx);
      console.log(`  SET   ${key}`);
    } catch (e) {
      if (e.message?.includes('already exists')) {
        console.log(`  EXISTS ${key}`);
      } else {
        console.warn(`  FAIL  ${key}: ${e.message}`);
      }
    }
  }

  // 5. Deploy
  console.log('\n=== 5. Deploying ===');
  const deployResult = await deployFromSpecification({
    service_id: serviceId,
    source: {
      type: 'BUILD_FROM_SOURCE',
      build_from_source: {
        source: {
          type: 'GITHUB',
          github: { repo_id: repoId, ref: 'master' },
        },
        dockerfile: { content: DOCKERFILE },
      },
    },
    env: [],
  }, ctx);
  console.log('Deploy response:', deployResult);

  // 6. Wait for service
  console.log('\n=== 6. Waiting for Service (up to 5 min) ===');
  const status = await waitForServicesRunning({ serviceIds: [serviceId], timeout: 300000, pollInterval: 10000 }, ctx);
  console.log('Status:', status);

  // 7. Show domain
  console.log('\n=== 7. Domain ===');
  const detail = JSON.parse(await getService({ serviceId }, ctx));
  const domains = detail.service?.domains || [];
  if (domains.length > 0) {
    const domain = domains[0].domain;
    console.log(`Backend live at: https://${domain}`);
    console.log(`API base URL: https://${domain}/api/v1`);
  } else {
    console.log('No domain assigned yet. Check Zeabur dashboard.');
  }

  console.log('\nDone');
}

main().catch(e => {
  console.error('Fatal:', e.message);
  process.exit(1);
});
