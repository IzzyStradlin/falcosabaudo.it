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

$rssUrl = 'https://falcosabaudo.forumfree.it/rss.php';
$rssContent = fetchUrl($rssUrl);
if ($rssContent === null) {
    renderError('Impossibile caricare il feed del forum.');
}

libxml_use_internal_errors(true);
$xml = simplexml_load_string($rssContent);
if ($xml === false) {
    renderError('Feed del forum non valido.');
}

$count = 0;
foreach ($xml->channel->item as $item) {
    if ($count++ >= 3) {
        break;
    }
    $title = htmlspecialchars((string)$item->title, ENT_QUOTES, 'UTF-8');
    $link = htmlspecialchars((string)$item->link, ENT_QUOTES, 'UTF-8');
    $pubDate = (string)$item->pubDate;
    $date = date('d/m/Y H:i', strtotime($pubDate));

    echo '<div class="forum-item p-2 rounded">';
    echo '<a href="' . $link . '" class="block" target="_blank" rel="noopener">';
    echo '<h4 class="forum-title text-sm font-medium text-yellow-400 hover:text-yellow-300">' . $title . '</h4>';
    echo '<div class="flex items-center justify-between mt-1">';
    echo '<span class="text-xs text-green-200">Forum</span>';
    echo '<span class="text-xs text-green-200">' . htmlspecialchars($date, ENT_QUOTES, 'UTF-8') . '</span>';
    echo '</div>';
    echo '</a>';
    echo '</div>';
}

if ($count === 0) {
    renderError('Nessuna discussione trovata.');
}
