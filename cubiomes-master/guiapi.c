/*
 * guiapi.c - GUI向けの薄いラッパーAPI (GUI-facing thin wrapper API)
 *
 * cubiomes本体の複雑な構造体(Generator, Range等)をPython/ctypesから
 * 直接触らずに済むよう、単純な引数だけの関数として再公開する。
 * (Re-exposes cubiomes functionality as simple flat functions so that
 *  Python/ctypes callers don't need to know the internal C structs.)
 */
#include <stdlib.h>
#include <string.h>
#include <stdint.h>

#include "generator.h"
#include "finders.h"
#include "util.h"

#ifdef __cplusplus
extern "C" {
#endif

/* 指定座標のバイオームIDを返す (block座標, scale=1) */
int gc_biome_at(int mc, uint32_t flags, int dim, uint64_t seed,
                int scale, int x, int y, int z)
{
    Generator g;
    setupGenerator(&g, mc, flags);
    applySeed(&g, dim, seed);
    return getBiomeAt(&g, scale, x, y, z);
}

/* バイオームIDから名前(英語のバイオームID文字列)を返す */
const char *gc_biome_name(int mc, int id)
{
    const char *s = biome2str(mc, id);
    return s ? s : "unknown";
}

/* MCバージョン列挙値から名前を返す */
const char *gc_mc_name(int mc)
{
    const char *s = mc2str(mc);
    return s ? s : "unknown";
}

/*
 * 中心座標(cx, cz)を中心に width x height (ブロック単位, scale=4のバイオーム格子)
 * の範囲を生成し、PPM画像として outPath に保存する。
 * pixPerCell: バイオーム1マスあたりのピクセル数 (見やすさ用の拡大率)
 * 戻り値: 0=成功, 非0=失敗
 */
int gc_generate_map_ppm(int mc, uint32_t flags, int dim, uint64_t seed,
                         int cx, int cz, int width, int height,
                         int pixPerCell, const char *outPath)
{
    if (width <= 0 || height <= 0 || pixPerCell <= 0)
        return -1;

    Generator g;
    setupGenerator(&g, mc, flags);
    applySeed(&g, dim, seed);

    Range r;
    r.scale = 4;
    r.x = cx - width/2;
    r.z = cz - height/2;
    r.sx = width;
    r.sz = height;
    r.y = 15; /* 海面付近の1枚 (a single plane near sea level) */
    r.sy = 1;

    int *biomeIds = allocCache(&g, r);
    if (!biomeIds)
        return -2;

    int err = genBiomes(&g, biomeIds, r);
    if (err)
    {
        free(biomeIds);
        return -3;
    }

    unsigned char biomeColors[256][3];
    initBiomeColors(biomeColors);

    int imgW = pixPerCell * r.sx;
    int imgH = pixPerCell * r.sz;
    unsigned char *rgb = (unsigned char *) malloc((size_t)3 * imgW * imgH);
    if (!rgb)
    {
        free(biomeIds);
        return -4;
    }

    biomesToImage(rgb, biomeColors, biomeIds, r.sx, r.sz, pixPerCell, 0);
    int saveErr = savePPM(outPath, rgb, imgW, imgH);

    free(rgb);
    free(biomeIds);
    return saveErr;
}

/*
 * 指定した構造物タイプについて、原点付近のリージョンを regionRadius 分
 * 探索し、見つかった理論上の生成位置(区画座標)を配列 outX/outZ に書き込む。
 * これは公式READMEのサンプルと同じ考え方の簡易探索であり、
 * 地形都合による生成失敗(1.18+の砂漠ピラミッド等)までは判定しない近似値。
 * 戻り値: 見つかった件数
 */
int gc_find_structures_near_origin(int structType, int mc, int dim,
                                    uint32_t flags, uint64_t seed,
                                    int regionRadius,
                                    int *outX, int *outZ, int maxResults)
{
    Generator g;
    setupGenerator(&g, mc, flags);
    applySeed(&g, dim, seed);

    int found = 0;
    for (int rz = -regionRadius; rz <= regionRadius && found < maxResults; rz++)
    {
        for (int rx = -regionRadius; rx <= regionRadius && found < maxResults; rx++)
        {
            Pos p;
            if (!getStructurePos(structType, mc, seed, rx, rz, &p))
                continue;
            if (!isViableStructurePos(structType, &g, p.x, p.z, 0))
                continue;
            outX[found] = p.x;
            outZ[found] = p.z;
            found++;
        }
    }
    return found;
}

int gc_find_structures_in_area(int structType, int mc, int dim,
                               uint32_t flags, uint64_t seed,
                               int minX, int minZ, int maxX, int maxZ,
                               int *outX, int *outZ, int maxResults)
{
    if (minX > maxX || minZ > maxZ || maxResults <= 0)
        return 0;

    StructureConfig sconf;
    if (!getStructureConfig(structType, mc, &sconf))
        return 0;

    int regionBlocks = sconf.regionSize * 16;
    int regX0 = floordiv(minX, regionBlocks) - 1;
    int regX1 = floordiv(maxX, regionBlocks) + 1;
    int regZ0 = floordiv(minZ, regionBlocks) - 1;
    int regZ1 = floordiv(maxZ, regionBlocks) + 1;

    Generator g;
    setupGenerator(&g, mc, flags);
    applySeed(&g, dim, seed);

    int found = 0;
    for (int rz = regZ0; rz <= regZ1 && found < maxResults; rz++)
    {
        for (int rx = regX0; rx <= regX1 && found < maxResults; rx++)
        {
            Pos p;
            if (!getStructurePos(structType, mc, seed, rx, rz, &p))
                continue;
            if (p.x < minX || p.x > maxX || p.z < minZ || p.z > maxZ)
                continue;
            if (!isViableStructurePos(structType, &g, p.x, p.z, 0))
                continue;
            outX[found] = p.x;
            outZ[found] = p.z;
            found++;
        }
    }
    return found;
}

int gc_find_seed_for_structure(int structType, int mc,
                                const int *posX, const int *posZ, int posCount,
                                uint64_t startSeed, uint64_t endSeed,
                                int tolerance, uint64_t *seedOut)
{
    if (posCount <= 0 || !posX || !posZ || !seedOut || endSeed < startSeed)
        return 0;

    Pos *positions = malloc(sizeof(Pos) * (size_t)posCount);
    if (!positions)
        return 0;

    for (int i = 0; i < posCount; i++)
    {
        positions[i].x = posX[i];
        positions[i].z = posZ[i];
    }

    int found = findSeedForStructure(structType, mc, positions, posCount,
                                     startSeed, endSeed, tolerance, seedOut);
    free(positions);
    return found;
}

const char *gc_struct_name(int structType)
{
    const char *s = struct2str(structType);
    return s ? s : "unknown";
}

#ifdef __cplusplus
}
#endif
