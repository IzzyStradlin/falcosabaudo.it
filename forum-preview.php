<?php
function fetchUrl($url) {
    $ch = curl_init($url);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_FOLLOWLOCATION, true);
    curl_setopt($ch, CURLOPT_TIMEOUT, 15);
    curl_setopt($ch, CURLOPT_USERAGENT, 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36');
    curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, true);
    curl_setopt($ch, CURLOPT_SSL_VERIFYHOST, 2);

    $result = curl_exec($ch);
    $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);

    if ($result === false || $httpCode !== 200) {
        return null;
    }

    return $result;
}

function renderError($message) {
    echo '<div class="text-center text-red-300 py-2">';
    echo '<p class="text-sm">' . htmlspecialchars($message, ENT_QUOTES, 'UTF-8') . '</p>';
    echo '</div>';
    exit;
}

$html = fetchUrl('https://falcosabaudo.forumfree.it/');
if ($html === null) {
    renderError('Impossibile caricare il forum.');
}

libxml_use_internal_errors(true);
$doc = new DOMDocument();
if (!$doc->loadHTML($html)) {
    renderError('Errore nel parsing della pagina del forum.');
}

$xpath = new DOMXPath($doc);
$items = [];

foreach ($xpath->query('//div[contains(@class, "zz")]') as $row) {
    $linkNode = $xpath->query('.//div[contains(@class, "where")]//a', $row)->item(0);
    $dateNode = $xpath->query('.//div[contains(@class, "when")]', $row)->item(0);

    if (!$linkNode) {
        continue;
    }

    $href = $linkNode->getAttribute('href');
    $title = trim($linkNode->textContent);
    $published = $dateNode ? trim($dateNode->textContent) : '';

    if (!$href || !$title) {
        continue;
    }

    if (strpos($href, '/') === 0) {
        $href = 'https://falcosabaudo.forumfree.it' . $href;
    }

    $items[] = [
        'title' => $title,
        'link' => $href,
        'published' => $published,
    ];

    if (count($items) >= 4) {
        break;
    }
}

if (empty($items)) {
    renderError('Nessun topic trovato nel forum.');
}

foreach ($items as $item) {
    $title = htmlspecialchars($item['title'], ENT_QUOTES, 'UTF-8');
    $link = htmlspecialchars($item['link'], ENT_QUOTES, 'UTF-8');
    $published = htmlspecialchars($item['published'], ENT_QUOTES, 'UTF-8');

    echo '<div class="topic-item p-2 rounded">';
    echo '<a href="' . $link . '" class="block text-sm text-green-200 hover:text-green-100" target="_blank" rel="noopener">';
    echo '<div class="flex justify-between space-x-2">';
    echo '  <span class="truncate">' . $title . '</span>';
    echo '  <span class="text-xs text-green-300">' . $published . '</span>';
    echo '</div>';
    echo '</a>';
    echo '</div>';
}
