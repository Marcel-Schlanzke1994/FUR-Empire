import js from '@eslint/js';
import globals from 'globals';

export default [js.configs.recommended,{
  files:['static/*.js'],
  languageOptions:{ecmaVersion:2022,sourceType:'script',globals:globals.browser},
  rules:{'no-unused-vars':['error',{argsIgnorePattern:'^_',varsIgnorePattern:'^(systemTabs|initSystems|systemsView|bindSystems)$'}],'no-var':'error','prefer-const':'error','eqeqeq':['error','always']}
},{
  files:['static/app.js'],
  languageOptions:{globals:{systemTabs:'readonly',initSystems:'readonly',systemsView:'readonly',bindSystems:'readonly'}}
},{
  files:['static/community.js'],
  languageOptions:{globals:{state:'readonly',csrf:'readonly',tab:'readonly',api:'readonly',notify:'readonly',command:'readonly',render:'readonly',refresh:'readonly',escapeHtml:'readonly',names:'readonly',icons:'readonly',number:'readonly'}}
}];
