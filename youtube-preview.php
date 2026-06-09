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

$channelUrl = 'https://www.youtube.com/@FALCOSABAUDOTV-v5y';
$page = fetchUrl($channelUrl);
if ($page === null) {
    renderError('Impossibile ottenere la pagina del canale YouTube.');
}

if (!preg_match('/"externalId"\s*:\s*"(UC[^"]+)"/', $page, $matches)) {
    renderError('Impossibile ricavare l\'ID del canale YouTube.');
}

$channelId = $matches[1];
$rssUrl = "https://www.youtube.com/feeds/videos.xml?channel_id={$channelId}";
$rssContent = fetchUrl($rssUrl);
if ($rssContent === null) {
    renderError('Impossibile caricare il feed YouTube.');
}

libxml_use_internal_errors(true);
$xml = simplexml_load_string($rssContent);
if ($xml === false) {
    renderError('Feed YouTube non valido.');
}

$items = array();
$namespace = 'http://www.youtube.com/xml/schemas/2015';
$count = 0;
foreach ($xml->entry as $entry) {
    if ($count++ >= 3) {
        break;
    }
    $videoId = (string)$entry->children($namespace)->videoId;
    $title = (string)$entry->title;
    $link = (string)$entry->link['href'];
    $published = date('d/m/Y H:i', strtotime((string)$entry->published));
    $items[] = compact('videoId', 'title', 'link', 'published');
}

if (empty($items)) {
    renderError('Nessun video trovato nel canale YouTube.');
}

foreach ($items as $video) {
    $videoTitle     = htmlspecialchars($video['title'], ENT_QUOTES, 'UTF-8');
    $videoUrl       = htmlspecialchars($video['link'], ENT_QUOTES, 'UTF-8');
    $videoId        = htmlspecialchars($video['videoId'], ENT_QUOTES, 'UTF-8');
    $published      = htmlspecialchars($video['published'], ENT_QUOTES, 'UTF-8');
    $thumbnailUrl   = "https://i.ytimg.com/vi/{$videoId}/mqdefault.jpg";

    echo '<div class="video-item p-2 rounded">';
    echo '<a href="' . $videoUrl . '" class="block" target="_blank" rel="noopener">';
    echo '<div class="flex space-x-2">';
    echo '  <div class="flex-shrink-0">';
    echo '    <img src="' . $thumbnailUrl . '" alt="' . $videoTitle . '" class="w-20 h-14 object-cover rounded">';
    echo '  </div>';
    echo '  <div class="flex-grow min-w-0">';
    echo '    <h4 class="video-title text-sm font-medium text-red-500 hover:text-red-400">' . $videoTitle . '</h4>';
    echo '    <div class="flex items-center justify-between mt-1">';
    echo '      <span class="text-xs text-green-200">YouTube</span>';
    echo '      <span class="text-xs text-green-200">' . $published . '</span>';
    echo '    </div>';
    echo '  </div>';
    echo '</div>';
    echo '</a>';
    echo '</div>';
}
