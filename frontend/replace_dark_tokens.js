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
      // Replace hardcoded dark backgrounds
      .replace(/dark:bg-background/g, 'dark:bg-background')
      .replace(/dark:bg-card/g, 'dark:bg-card')
      .replace(/dark:bg-muted/g, 'dark:bg-muted')
      .replace(/dark:bg-muted/g, 'dark:bg-muted')
      // Replace hardcoded dark borders
      .replace(/dark:border-border/g, 'dark:border-border')
      .replace(/dark:border-border/g, 'dark:border-border')
      .replace(/dark:border-border/g, 'dark:border-border')
      // Replace hardcoded dark divides
      .replace(/dark:divide-border/g, 'dark:divide-border')
      .replace(/dark:divide-border/g, 'dark:divide-border');
    
    // Also replace Tooltip specific arrow borders
    newContent = newContent
      .replace(/dark:border-t-muted/g, 'dark:border-t-muted')
      .replace(/dark:border-b-muted/g, 'dark:border-b-muted')
      .replace(/dark:border-l-muted/g, 'dark:border-l-muted')
      .replace(/dark:border-r-muted/g, 'dark:border-r-muted');

    if (content !== newContent) {
      fs.writeFileSync(file, newContent, 'utf8');
      filesChanged++;
      console.log(`Updated ${file}`);
    }
  });
  console.log(`Done. Updated ${filesChanged} files.`);
});
