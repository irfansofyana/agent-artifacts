#!/usr/bin/env node
import {existsSync,mkdirSync,readFileSync,writeFileSync,rmSync} from 'node:fs';
import {dirname,join,resolve} from 'node:path';
import {fileURLToPath} from 'node:url';
import {renderArtifact,renderHome} from './render-site.mjs';
import {validateEntry} from './site-model.mjs';
const root=resolve(process.env.ARTIFACT_REPO_ROOT||join(dirname(fileURLToPath(import.meta.url)),'..'));
function usage(){console.log('Usage: node scripts/add-artifact.mjs --slug name --title "Title" --description "Description" --file /path/to/content-fragment.html [--date YYYY-MM-DD] [--type html]');}
function parse(argv){const result={};for(let i=0;i<argv.length;i++){
 const key=argv[i];if(key==='--help'){result.help=true;continue}
 if(!['--slug','--title','--description','--file','--date','--type'].includes(key)||!argv[i+1]||argv[i+1].startsWith('--'))throw Error(`Invalid or missing argument: ${key}`);
 result[key.slice(2)]=argv[++i];
}return result}
function main(){
 const args=parse(process.argv.slice(2));if(args.help){usage();return}
 for(const key of ['slug','title','description','file'])if(!args[key])throw Error(`Missing required --${key}`);
 const source=resolve(args.file);if(!existsSync(source))throw Error(`Input does not exist: ${source}`);
 const fragment=readFileSync(source,'utf8');
 if(/<!doctype\b|<html\b|<head\b|<body\b/i.test(fragment))throw Error('Provide an HTML content fragment, not a full document; migrate body content into src/artifacts/<slug>/content.html.');
 const manifestPath=join(root,'artifacts.json'),original=readFileSync(manifestPath,'utf8');
 const manifest=JSON.parse(original);if(!Array.isArray(manifest.artifacts))throw Error('Manifest artifacts must be an array');
 const prior=manifest.artifacts.find(e=>e.slug===args.slug);
 const entry={title:args.title,slug:args.slug,description:args.description,createdAt:args.date||prior?.createdAt||new Date().toISOString().slice(0,10),type:args.type||prior?.type||'html',url:`artifacts/${args.slug}/`};
 validateEntry(entry,root);
 const artifacts=prior?manifest.artifacts.map(e=>e.slug===entry.slug?entry:e):[entry,...manifest.artifacts];
 if(new Set(artifacts.map(e=>e.slug)).size!==artifacts.length)throw Error('Duplicate manifest slug');
 const dest=join(root,'src/artifacts',entry.slug,'content.html'),page=join(root,'artifacts',entry.slug,'index.html'),home=join(root,'index.html');
 const css=existsSync(join(root,'src/artifacts',entry.slug,'module.css'))?`../../src/artifacts/${entry.slug}/module.css`:'';
 const js=existsSync(join(root,'src/artifacts',entry.slug,'module.js'))?`../../src/artifacts/${entry.slug}/module.js`:'';
 const writes=[[dest,fragment],[page,renderArtifact(entry,fragment,{moduleCss:css,moduleJs:js})],[home,renderHome({artifacts})],[manifestPath,JSON.stringify({...manifest,artifacts},null,2)+'\n']];
 const previous=writes.map(([p])=>existsSync(p)?readFileSync(p):null);
 try{for(const [p,text] of writes){mkdirSync(dirname(p),{recursive:true});writeFileSync(p,text)}}catch(e){for(let i=0;i<writes.length;i++){const [p]=writes[i];if(previous[i]===null)rmSync(p,{force:true});else writeFileSync(p,previous[i])}throw e}
 console.log(`Local draft generated: artifacts/${entry.slug}/index.html`);
 console.log('Run npm test && npm run validate && npm run test:browser before proposing publication. No push performed.');
}
try{main()}catch(e){console.error(e.message);process.exitCode=1}
