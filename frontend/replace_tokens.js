const fs = require('fs');
const path = require('path');

const walk = (dir, done) => {
  let results = [];
  fs.readdir(dir, (err, list) => {
    if (err) return done(err);
    let i = 0;
    (function next() {
      let file = list[i++];
      if (!file) return done(null, results);
      file = path.resolve(dir, file);
      fs.stat(file, (err, stat) => {
        if (stat && stat.isDirectory()) {
          // ignore node_modules and .next
          if (file.includes('node_modules') || file.includes('.next') || file.includes('.git')) {
            next();
          } else {
            walk(file, (err, res) => {
              results = results.concat(res);
              next();
            });
          }
        } else {
          if (file.endsWith('.tsx') || file.endsWith('.ts') || file.endsWith('.jsx') || file.endsWith('.js')) {
            results.push(file);
          }
          next();
        }
      });
    })();
  });
};

walk('d:\\Đồ án\\ChurnPrediction\\frontend', (err, results) => {
  if (err) throw err;
  let filesChanged = 0;
  results.forEach(file => {
    let content = fs.readFileSync(file, 'utf8');
    let newContent = content
      .replace(/dark:text-foreground/g, 'dark:text-foreground')
      .replace(/text-primary-foreground/g, 'text-primary-foreground')
      .replace(/bg-background/g, 'bg-background')
      .replace(/bg-background/g, 'bg-background');
    
    if (content !== newContent) {
      fs.writeFileSync(file, newContent, 'utf8');
      filesChanged++;
      console.log(`Updated ${file}`);
    }
  });
  console.log(`Done. Updated ${filesChanged} files.`);
});
