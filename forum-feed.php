<?php
// Mostra le ultime discussioni dal feed RSS del forum Falco Sabaudo
$rss_url = 'https://falcosabaudo.forumfree.it/rss.php';
$rss = simplexml_load_file($rss_url);
if ($rss === false) {
    echo '<div style="color:red">Impossibile caricare il feed RSS.</div>';
    return;
}
echo '<div class="bg-green-800 p-4 rounded shadow">';
echo '<h2 class="text-2xl font-bold mb-4">Ultime dal Forum</h2>';
echo '<ul class="list-disc ml-6">';
$count = 0;
foreach ($rss->channel->item as $item) {
    if ($count++ >= 8) break; // Mostra solo gli ultimi 8 post
    $title = htmlspecialchars($item->title);
    $link = htmlspecialchars($item->link);
    $date = date('d/m/Y H:i', strtotime($item->pubDate));
    echo "<li><a href='$link' target='_blank' rel='noopener' class='underline text-yellow-400'>$title</a> <span class='text-xs text-green-300'>($date)</span></li>";
}
echo '</ul>';
echo '</div>';
?>
